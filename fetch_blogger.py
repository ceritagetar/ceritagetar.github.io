import os
import re
import json
import requests
from html.parser import HTMLParser

API_KEY = os.environ.get('BLOGGER_API_KEY')
BLOG_ID = os.environ.get('BLOG_ID')
POSTS_PER_PAGE = 10

if not API_KEY or not BLOG_ID:
    raise EnvironmentError("BLOGGER_API_KEY dan BLOG_ID harus tersedia sebagai environment variable.")

os.makedirs("data", exist_ok=True)
os.makedirs("posts", exist_ok=True)
os.makedirs("labels", exist_ok=True)

def sanitize(text):
    return re.sub(r'\W+', '-', text.lower()).strip('-')

def strip_html(html):
    return re.sub("<[^<]+?>", "", html)

class ImageExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.thumbnail = None

    def handle_starttag(self, tag, attrs):
        if tag == 'img' and not self.thumbnail:
            for attr in attrs:
                if attr[0] == 'src':
                    self.thumbnail = attr[1]

def extract_thumbnail(html):
    parser = ImageExtractor()
    parser.feed(html)
    return parser.thumbnail or "https://via.placeholder.com/600x300?text=No+Image"

def fetch_all_posts():
    posts = []
    page_token = ''
    while True:
        url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={API_KEY}&maxResults=50"
        if page_token:
            url += f"&pageToken={page_token}"
        res = requests.get(url)
        if res.status_code != 200:
            raise Exception(f"Gagal ambil data: {res.status_code} {res.text}")
        data = res.json()
        posts.extend(data.get("items", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    with open("data/posts.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    return posts

def render_labels(labels, prefix=''):
    if not labels:
        return ""
    html = '<div class="post-labels">'
    for label in labels:
        html += f'<a href="{prefix}labels/{sanitize(label)}.html" class="label">{label}</a> '
    html += '</div>'
    return html

def generate_post_page(post):
    filename = f"{sanitize(post['title'])}-{post['id']}.html"
    filepath = os.path.join("posts", filename)
    thumbnail = extract_thumbnail(post["content"])
    labels = render_labels(post.get("labels", []), prefix="../")
    description = strip_html(post['content'])[:150]
    canonical_url = f"https://example.com/posts/{filename}"

    html = f"""<!DOCTYPE html>
<html lang='id'>
<head>
  <meta charset='UTF-8'>
  <title>{post['title']}</title>
  <meta name='description' content='{description}'>
  <link rel='canonical' href='{canonical_url}'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <link href='https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap' rel='stylesheet'>
  <link rel='stylesheet' href='../assets/style.css'>
</head>
<body>
  <header><h1 class='site-title'>Blog Saya</h1></header>
  <main>
    <div class='post-detail'>
      <h1 class='post-title'>{post['title']}</h1>
      {labels}
      <div class='post-content'>{post['content']}</div>
    </div>
  </main>
  <footer><p>&copy; 2025 Blog Saya</p></footer>
</body>
</html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filename

def generate_index_pages(posts):
    total_pages = (len(posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    for i in range(total_pages):
        page_posts = posts[i*POSTS_PER_PAGE:(i+1)*POSTS_PER_PAGE]
        fname = "index.html" if i == 0 else f"page{i+1}.html"

        html = f"""<!DOCTYPE html>
<html lang='id'>
<head>
  <meta charset='UTF-8'>
  <title>Beranda - Halaman {i+1}</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <link href='https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap' rel='stylesheet'>
  <link rel='stylesheet' href='assets/style.css'>
</head>
<body>
  <header><h1 class='site-title'>Blog Saya</h1></header>
  <main>"""

        for post in page_posts:
            post_file = generate_post_page(post)
            title = post['title']
            snippet = strip_html(post['content'])[:150]
            thumb = extract_thumbnail(post['content'])
            labels = render_labels(post.get("labels", []))

            html += f"""
  <article class='post-item'>
    <div class='post-thumbnail'>
      <a href='posts/{post_file}'><img src='{thumb}' alt='Thumbnail untuk {title}'></a>
    </div>
    <div class='post-info'>
      <h2 class='post-title'><a href='posts/{post_file}'>{title}</a></h2>
      {labels}
      <p class='post-snippet'>{snippet}... <a href='posts/{post_file}'>Selengkapnya</a></p>
    </div>
  </article>"""

        html += f"""
  </main>
  <footer><p>&copy; 2025 Blog Saya</p></footer>
</body>
</html>"""

        with open(fname, "w", encoding="utf-8") as f:
            f.write(html)

def generate_label_pages(posts):
    label_map = {}
    for post in posts:
        for label in post.get("labels", []):
            label_map.setdefault(label, []).append(post)

    for label, items in label_map.items():
        fname = f"labels/{sanitize(label)}.html"
        html = f"""<!DOCTYPE html>
<html lang='id'>
<head>
  <meta charset='UTF-8'>
  <title>Kategori: {label}</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <link href='https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap' rel='stylesheet'>
  <link rel='stylesheet' href='../assets/style.css'>
</head>
<body>
  <header><h1 class='site-title'>Kategori: {label}</h1></header>
  <main>"""

        for post in items:
            post_file = generate_post_page(post)
            title = post['title']
            snippet = strip_html(post['content'])[:150]
            thumb = extract_thumbnail(post['content'])

            html += f"""
  <article class='post-item'>
    <div class='post-thumbnail'>
      <a href='../posts/{post_file}'><img src='{thumb}' alt='Thumbnail untuk {title}'></a>
    </div>
    <div class='post-info'>
      <h2 class='post-title'><a href='../posts/{post_file}'>{title}</a></h2>
      <p class='post-snippet'>{snippet}... <a href='../posts/{post_file}'>Selengkapnya</a></p>
    </div>
  </article>"""

        html += f"""
  </main>
  <footer><p>&copy; 2025 Blog Saya</p></footer>
</body>
</html>"""

        with open(fname, "w", encoding="utf-8") as f:
            f.write(html)

if __name__ == '__main__':
    posts = fetch_all_posts()
    generate_index_pages(posts)
    generate_label_pages(posts)
    print(f"✅ {len(posts)} artikel berhasil digenerate.")
