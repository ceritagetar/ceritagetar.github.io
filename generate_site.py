import os
import requests
import json
from datetime import datetime
import re

API_KEY = os.getenv('BLOGGER_API_KEY')
BLOG_ID = os.getenv('BLOG_ID')

if not API_KEY or not BLOG_ID:
    print("Error: BLOGGER_API_KEY or BLOG_ID not set in environment variables.")
    exit(1)

BLOGGER_API_URL = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={API_KEY}&fetchBodies=true&maxResults=100"

print(f"Fetching posts from Blogger API for Blog ID: {BLOG_ID}")

try:
    response = requests.get(BLOGGER_API_URL)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"Error fetching data from Blogger API: {e}")
    exit(1)

posts_data = data.get('items', [])

output_dir = "posts"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = text.strip('-')
    return text

homepage_snippets = []

for post in posts_data:
    title = post.get('title', 'No Title')
    published_date_str = post.get('published', '')
    post_content_html = post.get('content', '')
    
    snippet = post_content_html[:200] + "..." if len(post_content_html) > 200 else post_content_html
    
    try:
        published_date = datetime.fromisoformat(published_date_str.replace('Z', '+00:00'))
        display_date = published_date.strftime('%d %B %Y')
    except ValueError:
        display_date = published_date_str

    post_slug = slugify(title)
    detail_page_url = f"/{output_dir}/{post_slug}.html"

    detail_html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; max-width: 800px; margin-left: auto; margin-right: auto; }}
        h1 {{ color: #333; }}
        .post-meta {{ font-size: 0.9em; color: #666; margin-bottom: 20px; }}
        .post-content img {{ max-width: 100%; height: auto; display: block; margin: 10px auto; }}
        a {{ color: #007bff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <header>
        <nav><a href="/">Home</a></nav>
        <h1>{title}</h1>
        <p class="post-meta">Published: {display_date}</p>
    </header>
    <main class="post-content">
        {post_content_html}
    </main>
    <footer>
        <p>&copy; {datetime.now().year} My Blogger Static Site. All rights reserved.</p>
    </footer>
</body>
</html>
"""
    detail_filename = f"{output_dir}/{post_slug}.html"
    try:
        with open(detail_filename, 'w', encoding='utf-8') as f:
            f.write(detail_html_content)
        print(f"Generated detail page: {detail_filename}")
    except IOError as e:
        print(f"Error saving detail page {detail_filename}: {e}")

    homepage_snippets.append(f"""
    <div class="post-snippet">
        <h2><a href="{detail_page_url}">{title}</a></h2>
        <p class="post-meta">Published: {display_date}</p>
        <p>{snippet} <a href="{detail_page_url}">Read More</a></p>
    </div>
    """)

homepage_content = "\n".join(homepage_snippets)
current_year = datetime.now().year

index_html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Blog Homepage</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; max-width: 800px; margin-left: auto; margin-right: auto; }}
        h1 {{ color: #333; }}
        .post-snippet {{ border-bottom: 1px solid #eee; padding-bottom: 20px; margin-bottom: 20px; }}
        .post-snippet:last-child {{ border-bottom: none; }}
        .post-snippet h2 {{ margin-top: 0; }}
        .post-meta {{ font-size: 0.9em; color: #666; }}
        a {{ color: #007bff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <header>
        <h1>Latest Blog Posts</h1>
    </header>
    <main>
        {homepage_content if homepage_content else "<p>No posts found.</p>"}
    </main>
    <footer>
        <p>&copy; {current_year} My Blogger Static Site. All rights reserved.</p>
    </footer>
</body>
</html>
"""

try:
    with open("index.html", 'w', encoding='utf-8') as f:
        f.write(index_html_content)
    print("Generated index.html")
except IOError as e:
    print(f"Error saving index.html: {e}")

print("Site generation complete.")
