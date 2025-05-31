import requests
import os
import re
import json
from html.parser import HTMLParser

API_KEY = os.environ.get('BLOGGER_API_KEY')
BLOG_ID = os.environ.get('BLOG_ID')

if not API_KEY or not BLOG_ID:
    raise EnvironmentError("Secrets BLOGGER_API_KEY dan BLOG_ID belum tersedia.")

DATA_DIR = 'data'
POST_DIR = 'posts'
LABEL_DIR = 'labels'
ASSETS_DIR = 'assets'
POSTS_JSON = os.path.join(DATA_DIR, 'posts.json')
POSTS_PER_PAGE = 10

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(LABEL_DIR, exist_ok=True)

# === Utilitas ===

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
    return parser.thumbnail or 'https://via.placeholder.com/600x200?text=No+Image'

def strip_html(html):
    return re.sub('<[^<]+?>', '', html)

def sanitize_filename(title):
    return re.sub(r'\W+', '-', title.lower()).strip('-')

def render_labels(labels):
    if not labels:
        return ""
    html = '<div class="labels">'
    for label in labels:
        label_filename = sanitize_filename(label)
        html += f'<span class="label"><a href="labels/{label_filename}.html">{label}</a></span> '
    html += "</div>"
    return html

# === Ambil semua postingan dari Blogger ===

def fetch_posts():
    all_posts = []
    page_token = ''

    while True:
        url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={API_KEY}&maxResults=50"
        if page_token:
            url += f"&pageToken={page_token}"

        res = requests.get(url)
        if res.status_code != 200:
            raise Exception(f"Gagal fetch: {res.status_code} {res.text}")

        data = res.json()
        items = data.get("items", [])
        all_posts.extend(items)
        page_token = data.get("nextPageToken")
        if not page_token:
            break

    with open(POSTS_JSON, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)

    return all_posts

# === Bangun halaman HTML ===

def generate_post_page(post):
    filename = f"{sanitize_filename(post['title'])}-{post['id']}.html"
    filepath = os.path.join(POST_DIR, filename)
    labels_html = render_labels(post.get("labels", []))
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <title>{post['title']}</title>
  <link rel="stylesheet" href="../assets/style.css">
</head>
<body>
  <header><h1>{post['title']}</h1><p><a href="../index.html">← Kembali</a></p></header>
  <main>
    <article>
      {labels_html}
      <div>{post['content']}</div>
    </article>
  </main>
  <footer><p>&copy; 2025 Blog</p></footer>
</body>
</html>""")
    return filename

def generate_index(posts):
    with open("index.html", 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <title>Beranda Blog</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <header><h1>Blog Saya</h1></header>
  <main><section>
""")
        for post in posts:
            filename = generate_post_page(post)
            snippet = strip_html(post['content'])[:150]
            thumb = extract_thumbnail(post['content'])
            labels = render_labels(post.get('labels', []))
            f.write(f"""
  <article>
    <a href="posts/{filename}">
      <img class="thumbnail" src="{thumb}" alt="">
      <h2>{post['title']}</h2>
    </a>
    {labels}
    <p>{snippet}... <a href="posts/{filename}">Baca selengkapnya</a></p>
  </article>""")
        f.write("""
  </section></main>
  <footer><p>&copy; 2025 Blog</p></footer>
</body>
</html>""")

def generate_label_pages(posts):
    label_map = {}

    for post in posts:
        if 'labels' in post:
            for label in post['labels']:
                label_map.setdefault(label, []).append(post)

    for label, label_posts in label_map.items():
        filename = f"{sanitize_filename(label)}.html"
        filepath = os.path.join(LABEL_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <title>Kategori: {label}</title>
  <link rel="stylesheet" href="../assets/style.css">
</head>
<body>
  <header><h1>Kategori: {label}</h1><p><a href="../index.html">← Kembali</a></p></header>
  <main><section>
""")
            for post in label_posts:
                post_file = generate_post_page(post)
                snippet = strip_html(post['content'])[:150]
                thumb = extract_thumbnail(post['content'])
                f.write(f"""
  <article>
    <a href="../posts/{post_file}">
      <img class="thumbnail" src="{thumb}" alt="">
      <h2>{post['title']}</h2>
    </a>
    <p>{snippet}... <a href="../posts/{post_file}">Baca selengkapnya</a></p>
  </article>""")
            f.write("""
  </section></main>
  <footer><p>&copy; 2025 Blog</p></footer>
</body>
</html>""")

# === Eksekusi ===

if __name__ == '__main__':
    print("📥 Mengambil artikel...")
    posts = fetch_posts()
    print("✅ Artikel diambil:", len(posts))
    generate_index(posts)
    generate_label_pages(posts)
    print("✅ Halaman index, posting, dan label selesai dibuat.")
