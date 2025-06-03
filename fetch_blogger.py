import requests
import os
import re
import json
import random
from html.parser import HTMLParser

# === Konfigurasi ===

API_KEY = os.environ.get('BLOGGER_API_KEY')
BLOG_ID = os.environ.get('BLOG_ID')

DATA_DIR = 'data'
POST_DIR = 'posts'
LABEL_DIR = 'labels'
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
        filename = sanitize_filename(label)
        html += f'<span class="label"><a href="/labels/{filename}-1.html">{label}</a></span> '
    html += "</div>"
    return html

def load_template(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def render_template(template, **context):
    for key, value in context.items():
        template = template.replace(f'{{{{ {key} }}}}', str(value))
    return template

def paginate(total_items, per_page):
    total_pages = (total_items + per_page - 1) // per_page
    return total_pages

def generate_pagination_links(base_url, current, total):
    html = '<nav class="pagination">'

    def page_link(page):
        cls = 'active' if page == current else ''
        suffix = "" if page == 1 and "index" in base_url else f"-{page}"
        return f'<a class="{cls}" href="{base_url}{suffix}.html">{page}</a>'

    if total <= 10:
        for i in range(1, total + 1):
            html += page_link(i)
    else:
        for i in range(1, 4):
            html += page_link(i)
        if current > 5:
            html += '<span>...</span>'
        if 4 <= current <= total - 3:
            html += page_link(current)
        if current < total - 4:
            html += '<span>...</span>'
        for i in range(total - 1, total + 1):
            if i > 3:
                html += page_link(i)

    html += '</nav>'
    return html

# === Komponen Custom (Head, Header, Sidebar, Footer) ===

def safe_load(path):
    return load_template(path) if os.path.exists(path) else ""

CUSTOM_HEAD = safe_load("custom_head.html")
CUSTOM_JS = safe_load("custom_js.html")
CUSTOM_HEADER = safe_load("custom_header.html")
CUSTOM_SIDEBAR = safe_load("custom_sidebar.html")
CUSTOM_FOOTER = safe_load("custom_footer.html")

# Gabungkan ke dalam satu blok <head>
CUSTOM_HEAD_FULL = CUSTOM_HEAD + CUSTOM_JS

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

# === Template ===

POST_TEMPLATE = load_template("post_template.html")
INDEX_TEMPLATE = load_template("index_template.html")
LABEL_TEMPLATE = load_template("label_template.html")

# === Halaman per postingan ===

def generate_post_page(post, all_posts):
    filename = f"{sanitize_filename(post['title'])}-{post['id']}.html"
    filepath = os.path.join(POST_DIR, filename)

    related = [p for p in all_posts if p['id'] != post['id']]
    related_sample = random.sample(related, min(5, len(related)))
    related_html = "<ul>" + "".join(
        f'<li><a href="{sanitize_filename(p["title"])}-{p["id"]}.html">{p["title"]}</a></li>'
        for p in related_sample
    ) + "</ul>"

    html = render_template(POST_TEMPLATE,
        title=post['title'],
        content=post['content'],
        labels=render_labels(post.get("labels", [])),
        related=related_html,
        custom_head=CUSTOM_HEAD_FULL,
        custom_header=CUSTOM_HEADER,
        custom_sidebar=CUSTOM_SIDEBAR,
        custom_footer=CUSTOM_FOOTER
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    return filename

# === Halaman index beranda ===

def generate_index(posts):
    total_pages = paginate(len(posts), POSTS_PER_PAGE)
    for page in range(1, total_pages + 1):
        start = (page - 1) * POSTS_PER_PAGE
        end = start + POSTS_PER_PAGE
        items = posts[start:end]
        items_html = ""
        for post in items:
            filename = generate_post_page(post, posts)
            snippet = strip_html(post['content'])[:150]
            thumb = extract_thumbnail(post['content'])
            labels = render_labels(post.get('labels', []))
            items_html += f"""
<article class="post">
  <div class="post-body">
    
    <div class="img-thumbnail"><img src="{thumb}" alt=""></div>
    <h2 class="post-title"><a href="posts/{filename}">{post['title']}</a></h2>
    <p class="post-snippet">{snippet}... <a href="posts/{filename}">Baca selengkapnya</a></p>
    <div class='label-line'>
      
    </div>
  </div>
</article>
"""
        pagination = generate_pagination_links("index", page, total_pages)
        html = render_template(INDEX_TEMPLATE,
            items=items_html,
            pagination=pagination,
            custom_head=CUSTOM_HEAD_FULL,
            custom_header=CUSTOM_HEADER,
            custom_sidebar=CUSTOM_SIDEBAR,
            custom_footer=CUSTOM_FOOTER
        )
        output_file = f"index.html" if page == 1 else f"index-{page}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

# === Halaman per label ===

def generate_label_pages(posts):
    label_map = {}
    for post in posts:
        if 'labels' in post:
            for label in post['labels']:
                label_map.setdefault(label, []).append(post)

    for label, label_posts in label_map.items():
        total_pages = paginate(len(label_posts), POSTS_PER_PAGE)
        for page in range(1, total_pages + 1):
            start = (page - 1) * POSTS_PER_PAGE
            end = start + POSTS_PER_PAGE
            items = label_posts[start:end]
            items_html = ""
            for post in items:
                filename = generate_post_page(post, posts)
                snippet = strip_html(post['content'])[:150]
                thumb = extract_thumbnail(post['content'])
                items_html += f"""
<article id="post-wrapper">
  <a href="../posts/{filename}">
    <img class="thumbnail" src="{thumb}" alt="">
    <h2>{post['title']}</h2>
  </a>
  <p>{snippet}... <a href="../posts/{filename}">Baca selengkapnya</a></p>
</article>
"""
            pagination = generate_pagination_links(
                f"{sanitize_filename(label)}", page, total_pages
            )
            html = render_template(LABEL_TEMPLATE,
                label=label,
                items=items_html,
                pagination=pagination,
                custom_head=CUSTOM_HEAD_FULL,
                custom_header=CUSTOM_HEADER,
                custom_sidebar=CUSTOM_SIDEBAR,
                custom_footer=CUSTOM_FOOTER
            )
            output_file = os.path.join(LABEL_DIR, f"{sanitize_filename(label)}-{page}.html")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

# === Eksekusi ===

if __name__ == '__main__':
    print("📥 Mengambil artikel...")
    posts = fetch_posts()
    print(f"✅ Artikel diambil: {len(posts)}")
    generate_index(posts)
    generate_label_pages(posts)
    print("✅ Halaman index, label, dan artikel selesai dibuat.")
