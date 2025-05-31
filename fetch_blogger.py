import requests
import json
import os

API_KEY = os.environ['BLOGGER_API_KEY']
BLOG_ID = os.environ['BLOG_ID']
OUTPUT_PATH = 'data/posts.json'

def fetch_posts():
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        posts = [{
            'id': post['id'],
            'title': post['title'],
            'content': post['content'],
            'url': post['url'],
            'published': post['published']
        } for post in data.get('items', [])]

        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)

        print(f"{len(posts)} posts saved.")
    else:
        print(f"Failed to fetch posts: {response.status_code} {response.text}")

if __name__ == '__main__':
    fetch_posts()
