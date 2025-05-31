import requests
import os
import re
from html.parser import HTMLParser

API_KEY = os.environ.get('BLOGGER_API_KEY')
BLOG_ID = os.environ.get('BLOG_ID')
POSTS_PER_PAGE = 10

if not API_KEY or not BLOG_ID:
    raise ValueError("BLOGGER_API_KEY dan BLOG_ID harus tersedia di environment variables")

# === Utility ===

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

# === Directories ===
os.makedirs("posts", exist_ok=True)
os.makedirs("assets", exist_ok=True)

with open("assets/style.css", "w", encoding="utf-8") as f:
    f.write("""<ISI CSS ANDA DI SINI>""")  # Tempatkan isi `style.css` di sini kalau ingin satu file

# === Fetch Posts with Pagination ===

def fetch_all_posts():
    posts = []
    token = ''
    while True:
        url = f'https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={API_KEY}&maxResults=50'
        if token:
            url += f'&pageToken={token}'

        res = requests.get(url)
        if res.status_code != 200:
            raise Exception(f"Gagal fetch: {res.status_code} {res.text}")

        data = res.json()
        items = data.get('items', [])
        posts.extend(items)

        token = data.get('nextPageToken')
        if not token:
            break

    return posts

# === Generate Files ===

def generate_post_page(post):
    filename = f"{sanitize_filename(post['title'])}-{post['id']}.html"
    filepath = os.path.join("posts", filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <title>{post['title']}</title>
  <link rel="stylesheet" href="../assets/style.css">
</head>
<body>
  <header>
    <h1>{post['title']}</h1>
    <p><a href="../index.html" style="color:white;">← Kembali ke Beranda</a></p>
  </header>
  <main>
    <section>
      <article>
        <div>{post['content']}</div>
      </article>
    </section>
  </main>
  <footer><p>&copy; 2025 Blog</p></footer>
</body>
</html>
""")
    return filename

def generate_index_pages(posts):
    total_pages = (len(posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE

    for page in range(total_pages):
        paginated_posts = posts[page * POSTS_PER_PAGE:(page + 1) * POSTS_PER_PAGE]
        filename = f"index.html" if page == 0 else f"page{page + 1}.html"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <title>Blog Saya - Halaman {page + 1}</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <header>
    <h1>Blog Saya</h1>
    <p>Selamat datang di blog</p>
  </header>
  <main>
    <section>
""")

            for post in paginated_posts:
                thumb = extract_thumbnail(post['content'])
                snippet = strip_html(post['content'])[:150]
                filename_post = generate_post_page(post)
                f.write(f"""
      <article>
        <a href="posts/{filename_post}">
          <img class="thumbnail" src="{thumb}" alt="Thumbnail">
          <h2>{post['title']}</h2>
        </a>
        <p>{snippet}... <a href="posts/{filename_post}">Baca selengkapnya</a></p>
      </article>
""")
            f.write("""    </section>
    <aside>
      <h3>Tentang</h3>
      <p>Blog ini berisi cerita, catatan, dan pemikiran sehari-hari.</p>
    </aside>
  </main>
  <nav class="pagination">""")

            for p in range(total_pages):
                link = "index.html" if p == 0 else f"page{p + 1}.html"
                active = 'class="active"' if p == page else ''
                f.write(f'<a href="{link}" {active}>{p + 1}</a>')

            f.write(f"""</nav>
  <footer><p>&copy; 2025 Blog Saya</p></footer>
</body>
</html>
""")

# === Jalankan Semua ===

if __name__ == '__main__':
    print("📥 Mengambil data dari Blogger...")
    all_posts = fetch_all_posts()
    print(f"✅ Total postingan: {len(all_posts)}")
    generate_index_pages(all_posts)
    print("✅ Selesai. HTML sudah digenerate.")
