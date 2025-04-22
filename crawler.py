import os
import time
import requests
import psycopg2
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

url = os.environ["TARGET_URL"]
interval = int(os.environ["CRAWL_INTERVAL"])

def load_sql(filename):
    with open(f"sql/{filename}", "r") as f:
        return f.read()

# Connect to DB
while True:
    try:
        db_conn = psycopg2.connect(
            host=os.environ["DB_HOST"],
            port=os.environ["DB_PORT"],
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"]
        )
        break
    except Exception:
        print("Waiting for DB...")
        time.sleep(2)

cur = db_conn.cursor()

# 1. Load schema
cur.execute(load_sql("init_schema.sql"))
db_conn.commit()

# 2. Load other SQL
sql_insert_author = load_sql("insert_author.sql")
sql_select_author = load_sql("select_author_id.sql")
sql_insert_quote = load_sql("insert_quote.sql")

def crawl():
    print(f"Crawling: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    quotes = soup.select("div.quote")

    results = []
    for q in quotes:
        text = q.find("span", class_="text").get_text()
        author = q.find("small", class_="author").get_text()
        results.append((text, author))
        print(f"{text} — {author}")

    save_to_db(results)

def save_to_db(quotes):
    for text, author_name in quotes:
        # Insert or get author_id
        cur.execute(sql_insert_author, (author_name,))
        result = cur.fetchone()

        if result:
            author_id = result[0]
        else:
            cur.execute(sql_select_author, (author_name,))
            author_id = cur.fetchone()[0]

        # Insert quote
        cur.execute(sql_insert_quote, (text, author_id))

    db_conn.commit()

if __name__ == "__main__":
    while True:
        crawl()
        print(f"Sleeping {interval}s...\n")
        time.sleep(interval)
