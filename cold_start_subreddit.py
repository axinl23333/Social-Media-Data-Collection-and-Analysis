import logging
from pyfaktory import Client, Consumer, Job, Producer
import time
import random
import sys

logger = logging.getLogger("faktory test")
logger.propagate = False
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)

'''
4chan to Reddit

Catalog -> front_page
Board -> subreddit
Thread -> post
Replies -> comments
'''

if __name__ == "__main__":
    subreddit = sys.argv[1]
    print(f"Cold starting catalog crawl for subreddit {subreddit}")
    # Default url for a Faktory server running locally
    faktory_server_url = "tcp://:password@localhost:7419"

    with Client(faktory_url=faktory_server_url, role="producer") as client:
        producer = Producer(client=client)
        job = Job(jobtype="reddit-crawl-catalog", args=(subreddit,), queue="reddit-crawl-catalog")
        producer.push(job)
