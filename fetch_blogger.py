import requests
import os
import re

API_KEY = os.environ['BLOGGER_API_KEY']
BLOG_ID = os.environ['BLOG_ID']
OUTPUT_DIR = '.'

POSTS_DIR = os.path.join(OUTPUT_DIR, 'posts')
os.makedirs(POSTS_DIR, exist_ok=True)

def sanitize_filename(title):
    return re.sub(r'\W+', '-', title.lower()).strip('-')

def fetch_posts():
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch: {response.status_code}, {response.text}")

    items = response.json().get('items', [])
    generate_index_html(items)

    for post in items:
        generate_post_html(post)

def generate_index_html(posts):
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write("<html><head><title>Blog</title></head><body>\n")
        f.write("<h1>Daftar Artikel</h1>\n<ul>\n")
        for post in posts:
            filename = f"posts/{sanitize_filename(post['title'])}-{post['id']}.html"
            snippet = re.sub(r'<[^>]+>', '', post['content'])[:150]
            f.write(f"<li><a href='{filename}'>{post['title']}</a><p>{snippet}...</p></li>\n")
        f.write("</ul>\n</body></html>")

def generate_post_html(post):
    filename = os.path.join(POSTS_DIR, f"{sanitize_filename(post['title'])}-{post['id']}.html")
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"<html><head><title>{post['title']}</title></head><body>\n")
        f.write(f"<a href='../index.html'>← Kembali</a>")
        f.write(f"<h1>{post['title']}</h1>\n")
        f.write(f"<div>{post['content']}</div>\n")
        f.write("</body></html>")

if __name__ == '__main__':
    fetch_posts()
