from reddit_client import RedditClient
import logging
from pyfaktory import Client, Consumer, Job, Producer
import datetime
import psycopg2
from psycopg2 import pool
from psycopg2.extras import execute_values
import requests



# these three lines allow psycopg to insert a dict into
# a jsonb coloumn
from psycopg2.extras import Json
from psycopg2.extensions import register_adapter

register_adapter(dict, Json)

# load in function for .env reading
from dotenv import load_dotenv


logger = logging.getLogger("Reddit client")
logger.propagate = False
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)

load_dotenv()

import os

FAKTORY_SERVER_URL = os.environ.get("FAKTORY_SERVER_URL")
DATABASE_URL = os.environ.get("DATABASE_URL2")


print(f"Connecting to Faktory at: {FAKTORY_SERVER_URL}")

'''
4chan to Reddit

Catalog -> front_page
Board -> subreddit
Thread -> thread
Post -> post
'''

"""
Return all the thread numbers from a catalog json object
"""

def thread_numbers_from_catalog(catalog):
    thread_numbers = []
    posts = catalog["data"]["children"]
    for post in posts:
        post_data = post["data"]
        post_number = post_data["id"]
        thread_numbers.append(post_number)

    return thread_numbers


"""
Return thread numbers that existed in previous but don't exist
in current
"""


def find_dead_threads(previous_catalog_thread_numbers, current_catalog_thread_numbers):
    dead_thread_numbers = set(previous_catalog_thread_numbers).difference(
        set(current_catalog_thread_numbers)
    )
    return dead_thread_numbers


"""
Crawl a given thread and get its json.
Insert the posts into db
"""
def reddit_crawl_thread(subreddit, thread_number):
    reddit_client = RedditClient() 
    try:
        thread_data = reddit_client.get_thread(subreddit, thread_number)
        
        logger.info(f"Thread: {subreddit}/{thread_number}/:\n{thread_data}")

        # really should use a connection pool
        conn = psycopg2.connect(dsn=DATABASE_URL)

        cur = conn.cursor()
        # now insert into db
        # iterate through the thread data and get all the post data

        # Post info
        post = thread_data[0]["data"]["children"][0]
        post_data = post.get("data", {})
        post_id = post_data.get("id")
        q_post = "INSERT INTO posts (subreddit, post_id) VALUES (%s, %s) RETURNING id"
        cur.execute(q_post, (subreddit, post_id))
        conn.commit()

        # Comment info
        for comment in thread_data[1]["data"]["children"]:
            comment_data = comment.get("data", {})
            comment_id = comment_data.get("id")
            q = "INSERT INTO comments (subreddit, post_id) VALUES (%s, %s) RETURNING id"
            cur.execute(q, (subreddit, comment_id))
            # commit our insert to the database.
            conn.commit()
    
            # it's often useful to know the id of the newly inserted
            # row. This is so you can launch other jobs that might
            # do additional processing.
            # e.g., to classify the toxicity of a post
            db_id = cur.fetchone()[0]
            logging.info(f"Inserted DB id: {db_id}")
    except Exception as e:
        logger.error(f"Error while crawling thread {subreddit}/{thread_number}: {e}")
    # close cursor connection
    cur.close()
    # close connection
    conn.close()


"""
Go out, grab the catalog for a given board, and figure out what threads we need
to collect.

For each thread to collect, enqueue a new job to crawl the thread.

Schedule catalog crawl to run again at some point in the future.
"""

def reddit_crawl_catalog(subreddit, previous_catalog_thread_numbers=[]):
    reddit_client = RedditClient()
    try:
        current_catalog = reddit_client.get_catalog(subreddit)
        logger.info(f"Current catalog: {current_catalog}")
        current_catalog_thread_numbers = thread_numbers_from_catalog(current_catalog)

        dead_threads = find_dead_threads(
            previous_catalog_thread_numbers, current_catalog_thread_numbers
        )
        logger.info(f"dead threads: {dead_threads}")

        # issue the crawl thread jobs for each dead thread
        crawl_thread_jobs = []
        with Client(faktory_url=FAKTORY_SERVER_URL, role="producer") as client:
            producer = Producer(client=client)
            for dead_thread in dead_threads:
                # see https://github.com/ghilesmeddour/faktory_worker_python/blob/main/src/pyfaktory/models.py
                # what a `Job` looks like
                job = Job(
                    jobtype="reddit-crawl-thread", args=(subreddit, dead_thread), queue="reddit-crawl-thread"
                )

                crawl_thread_jobs.append(job)

            producer.push_bulk(crawl_thread_jobs)

        # Schedule another catalog crawl to happen at some point in future
        with Client(faktory_url=FAKTORY_SERVER_URL, role="producer") as client:
            producer = Producer(client=client)
            # figure out how to use non depcreated methods on your own
            # run_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)
            run_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
            run_at = run_at.isoformat()[:-7] + "Z"
            logger.info(f"run_at = {run_at}")
            job = Job(
                jobtype="reddit-crawl-catalog",
                args=(subreddit, current_catalog_thread_numbers),
                queue="reddit-crawl-catalog",
                at=str(run_at),
            )
            producer.push(job)
    except Exception as e:
        logger.error(f"Error while crawling catalog for subreddit {subreddit}: {e}")

if __name__ == "__main__":
    #reddit_crawl_thread("politics", "1h7bmuc")
    try: 
        # we want to pull jobs off the queues and execute them
        # FOREVER (continuously)
        with Client(faktory_url=FAKTORY_SERVER_URL, role="consumer") as client:
            consumer = Consumer(
                client=client, queues=["reddit-crawl-catalog", "reddit-crawl-thread"], concurrency=5
            )
            consumer.register("reddit-crawl-catalog", reddit_crawl_catalog)
            consumer.register("reddit-crawl-thread", reddit_crawl_thread)

            # tell the consumer to pull jobs off queue and execute them!
            consumer.run()
    except Exception as e:
        logger.error(f"Error with consumer: {e}")
        

