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

# Direktori
os.makedirs("data", exist_ok=True)
os.makedirs("posts", exist_ok=True)
os.makedirs("labels", exist_ok=True)

# Load custom components
def load_component(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

HEAD_HTML = load_component("custom_head.html")
HEADER_HTML = load_component("custom_header.html")
SIDEBAR_HTML = load_component("custom_sidebar.html")
FOOTER_HTML = load_component("custom_footer.html")

# HTML Util
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

def strip_html(html):
    return re.sub("<[^<]+?>", "", html)

def sanitize(text):
    return re.sub(r'\W+', '-', text.lower()).strip('-')

def render_labels(labels, prefix=''):
    if not labels:
        return ""
    html = '<div class="labels">'
    for label in labels:
        html += f'<span class="label"><a href="{prefix}labels/{sanitize(label)}.html">{label}</a></span> '
    html += "</div>"
    return html

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

def generate_post_page(post):
    filename = f"{sanitize(post['title'])}-{post['id']}.html"
    filepath = os.path.join("posts", filename)
    thumbnail = extract_thumbnail(post["content"])
    labels = render_labels(post.get("labels", []), prefix="../")
    description = strip_html(post["content"])[:150]
    canonical_url = f"https://example.com/posts/{filename}"  # Ganti dengan domain Anda

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang=\"id\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{post['title']}</title>
  <meta name=\"description\" content=\"{description}\">
  <link rel=\"canonical\" href=\"{canonical_url}\">
  <meta property=\"og:title\" content=\"{post['title']}\">
  <meta property=\"og:description\" content=\"{description}\">
  <meta property=\"og:image\" content=\"{thumbnail}\">
  <meta property=\"og:type\" content=\"article\">
  <meta name=\"twitter:card\" content=\"summary_large_image\">
  <meta name=\"twitter:title\" content=\"{post['title']}\">
  <meta name=\"twitter:description\" content=\"{description}\">
  <meta name=\"twitter:image\" content=\"{thumbnail}\">
  <link rel=\"stylesheet\" href=\"../assets/style.css\">
  {HEAD_HTML}
</head>
<body>
  {HEADER_HTML}
  <main>
    <section>
      <h1>{post['title']}</h1>
      {labels}
      <div>{post['content']}</div>
    </section>
    <aside>{SIDEBAR_HTML}</aside>
  </main>
  {FOOTER_HTML}
</body>
</html>""")
    return filename

def generate_index_pages(posts):
    total_pages = (len(posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    for i in range(total_pages):
        page_posts = posts[i*POSTS_PER_PAGE:(i+1)*POSTS_PER_PAGE]
        fname = "index.html" if i == 0 else f"page{i+1}.html"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html lang=\"id\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Halaman {i+1}</title>
  <meta name=\"description\" content=\"Daftar artikel halaman {i+1}\">
  <link rel=\"stylesheet\" href=\"assets/style.css\">
  {HEAD_HTML}
</head>
<body>
  {HEADER_HTML}
  <main><section>""")
            for post in page_posts:
                post_file = generate_post_page(post)
                snippet = strip_html(post['content'])[:150]
                thumb = extract_thumbnail(post['content'])
                labels = render_labels(post.get("labels", []))
                f.write(f"""
  <article>
    <a href=\"posts/{post_file}\"><img class=\"thumbnail\" src=\"{thumb}\" alt=\"Thumbnail untuk {post['title']}\"><h2>{post['title']}</h2></a>
    {labels}
    <p>{snippet}... <a href=\"posts/{post_file}\">Baca selengkapnya</a></p>
  </article>""")
            f.write("</section><aside>{}</aside></main><nav class='pagination'>".format(SIDEBAR_HTML))
            for j in range(total_pages):
                page_name = "index.html" if j == 0 else f"page{j+1}.html"
                active = "class='active'" if j == i else ""
                f.write(f"<a href='{page_name}' {active}>{j+1}</a>")
            f.write(f"</nav>{FOOTER_HTML}</body></html>")

def generate_label_pages(posts):
    label_map = {}
    for post in posts:
        for label in post.get("labels", []):
            label_map.setdefault(label, []).append(post)

    for label, items in label_map.items():
        fname = f"labels/{sanitize(label)}.html"
        description = f"Artikel dalam kategori {label}"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html lang=\"id\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Kategori: {label}</title>
  <meta name=\"description\" content=\"{description}\">
  <link rel=\"stylesheet\" href=\"../assets/style.css\">
  {HEAD_HTML}
</head>
<body>
  {HEADER_HTML}
  <main><section><h1>Kategori: {label}</h1>""")
            for post in items:
                post_file = generate_post_page(post)
                snippet = strip_html(post['content'])[:150]
                thumb = extract_thumbnail(post['content'])
                f.write(f"""
  <article>
    <a href=\"../posts/{post_file}\"><img class=\"thumbnail\" src=\"{thumb}\" alt=\"Thumbnail untuk {post['title']}\"><h2>{post['title']}</h2></a>
    <p>{snippet}... <a href=\"../posts/{post_file}\">Baca selengkapnya</a></p>
  </article>""")
            f.write(f"</section><aside>{SIDEBAR_HTML}</aside></main>{FOOTER_HTML}</body></html>")

if __name__ == '__main__':
    posts = fetch_all_posts()
    generate_index_pages(posts)
    generate_label_pages(posts)
    print(f"✅ {len(posts)} artikel berhasil digenerate.")
