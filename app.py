import os
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
import psycopg2
from datetime import datetime

load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.getenv('DATABASE_URL2')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

@app.route('/')
def index():
    return "WELCOME TO THE reddit_crawler API"

@app.route('/posts')
def test_db_by_group():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT subreddit, COUNT(*) FROM posts GROUP BY subreddit;')

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        posts = [{"subreddit": row[0], "count": row[1]} for row in rows]
        return jsonify(posts)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/visualize/subreddits')
def visualize_subreddits():
    return render_template('visualize_subreddits.html')

@app.route('/dates')
def test_frequency_by_dates(): # SELECTING POST FREQUENCY BY DATES FOR R/POL
    try:
        # subreddit = request.args.get('subreddit', 'politics')


        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT subreddit, DATE(created_at) AS post_date, COUNT(*) AS post_count 
            FROM posts
            GROUP BY subreddit, DATE(created_at)
            ORDER BY post_date;
        ''')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        data = []

        for row in rows:
            clean_date = row[1].strftime("%Y-%m-%d")
            data.append({
                "subreddit": row[0],
                "post_date": clean_date,
                "post_count": row[2]
            })
        # dates = [{"subreddit": row[0], "post_date": row[1], "post_count": row[2]} for row in rows]
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/visualize/dates')
def visualize_dates():
    return render_template("visualize_dates.html")


if __name__ == '__main__':
    app.run(debug=True)
