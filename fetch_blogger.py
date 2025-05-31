import os
import re
import json
import requests
from html.parser import HTMLParser

# --- Konfigurasi Awal ---
API_KEY = os.environ.get('BLOGGER_API_KEY')
BLOG_ID = os.environ.get('BLOG_ID')
POSTS_PER_PAGE = 10


if not API_KEY or not BLOG_ID:
    raise EnvironmentError("BLOGGER_API_KEY dan BLOG_ID harus tersedia sebagai environment variable.")

# Direktori untuk menyimpan data dan halaman yang dihasilkan
os.makedirs("data", exist_ok=True)
os.makedirs("posts", exist_ok=True)
os.makedirs("labels", exist_ok=True)
os.makedirs("assets", exist_ok=True) # Pastikan direktori assets ada untuk CSS/JS

# --- Muat Komponen Kustom ---
# Pertimbangkan untuk menambahkan meta tag SEO ke custom_head.html
HEAD_HTML = load_component("custom_head.html")
HEADER_HTML = load_component("custom_header.html")
SIDEBAR_HTML = load_component("custom_sidebar.html")
FOOTER_HTML = load_component("custom_footer.html")

# --- Utilitas HTML untuk SEO ---

class ImageExtractor(HTMLParser):
    """
    Mengekstrak URL gambar pertama dari konten HTML untuk digunakan sebagai thumbnail.
    Menambahkan atribut 'alt' jika tidak ada untuk SEO gambar.
    """
    def __init__(self):
        super().__init__()
        self.thumbnail = None

    def handle_starttag(self, tag, attrs):
        if tag == 'img' and not self.thumbnail:
            img_src = None
            img_alt = ""
            for attr_name, attr_value in attrs:
                if attr_name == 'src':
                    img_src = attr_value
                if attr_name == 'alt':
                    img_alt = attr_value
            if img_src:
                self.thumbnail = img_src
                # Anda bisa menambahkan logika untuk memastikan alt text
                # Misalnya, jika alt kosong, gunakan judul postingan
                if not img_alt:
                    # Ini memerlukan judul postingan, yang mungkin belum tersedia di sini
                    # Pertimbangkan untuk mempassing judul postingan ke ImageExtractor jika diperlukan
                    pass

def extract_thumbnail(html, title=""):
    """
    Mengekstrak URL gambar pertama dari HTML dan menambahkan alt text jika tidak ada.
    """
    parser = ImageExtractor()
    parser.feed(html)
    thumb = parser.thumbnail
    if not thumb:
        return "https://via.placeholder.com/600x300?text=No+Image" # Placeholder jika tidak ada gambar
    # Anda bisa memanipulasi HTML di sini untuk menambahkan alt text ke gambar jika diperlukan
    # Namun, lebih baik dilakukan saat generating post_content jika sumbernya mengizinkan
    return thumb

def strip_html(html):
    """Menghapus tag HTML dari string."""
    return re.sub("<[^<]+?>", "", html)

def sanitize(text):
    """
    Membersihkan teks untuk URL slug.
    Menggunakan hyphen (-) sebagai pemisah dan menghilangkan karakter non-alfanumerik.
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text) # Hapus karakter non-alfanumerik kecuali spasi dan hyphen
    text = re.sub(r'\s+', '-', text) # Ganti spasi dengan hyphen
    return text.strip('-') # Hapus hyphen di awal atau akhir

def render_labels(labels, prefix=''):
    """
    Merender label sebagai tautan dengan struktur URL yang SEO-friendly.
    """
    if not labels:
        return ""
    html = '<div class="labels" itemprop="keywords">' # Menambahkan itemprop untuk schema.org
    for label in labels:
        # Gunakan sanitize untuk URL label
        html += f'<span class="label"><a href="{prefix}labels/{sanitize(label)}.html">{label}</a></span> '
    html += "</div>"
    return html

# --- Fungsi Pengambilan Data ---
def fetch_all_posts():
    """Mengambil semua postingan dari Blogger API."""
    posts = []
    page_token = ''
    print("Mulai mengambil postingan dari Blogger API...")
    while True:
        url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={API_KEY}&maxResults=50"
        if page_token:
            url += f"&pageToken={page_token}"
        
        try:
            res = requests.get(url, timeout=10) # Menambahkan timeout untuk keamanan
            res.raise_for_status() # Akan memunculkan HTTPError untuk status kode 4xx/5xx
        except requests.exceptions.RequestException as e:
            raise Exception(f"Gagal ambil data dari Blogger API: {e}")

        data = res.json()
        posts.extend(data.get("items", []))
        page_token = data.get("nextPageToken")
        
        if not page_token:
            break
    
    with open("data/posts.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"Berhasil mengambil {len(posts)} postingan.")
    return posts

# --- Fungsi Generasi Halaman ---

def generate_post_page(post):
    """
    Membuat halaman HTML individual untuk setiap postingan.
    Meningkatkan SEO dengan meta tag, canonical URL, dan schema.org markup.
    """
    # Menggunakan ID postingan untuk memastikan keunikan, bersama dengan judul yang bersih
    filename = f"{sanitize(post['title'])}-{post['id']}.html"
    filepath = os.path.join("posts", filename)
    
    post_url = f"{BASE_URL}posts/{filename}"
    thumbnail_url = extract_thumbnail(post['content'], post['title']) # Pass title for better alt text

    # Menggunakan deskripsi meta yang lebih baik
    # Batasi snippet menjadi panjang yang sesuai untuk meta description
    meta_description = strip_html(post.get('content', ''))[:160] + "..." if len(strip_html(post.get('content', ''))) > 160 else strip_html(post.get('content', ''))
    
    labels_html = render_labels(post.get("labels", []), prefix="../")

    # Waktu publikasi dan pembaruan untuk schema.org
    published_date = post.get('published', '')
    updated_date = post.get('updated', '')

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{post['title']} | Cerita Seks Dewasa</title>
  <meta name="description" content="{meta_description}">
  <link rel="canonical" href="{post_url}">
  <link rel="stylesheet" href="../assets/style.css">
  
  <meta property="og:title" content="{post['title']} | Cerita Seks Dewasa">
  <meta property="og:description" content="{meta_description}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{post_url}">
  <meta property="og:image" content="{thumbnail_url}">
  <meta property="og:site_name" content="Cerita Seks Dewasa">
  
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{post['title']} | Cerita Seks Dewasa">
  <meta name="twitter:description" content="{meta_description}">
  <meta name="twitter:image" content="{thumbnail_url}">
  
  {HEAD_HTML}
</head>
<body>
  {HEADER_HTML}
  <main>
    <article itemscope itemtype="http://schema.org/Article">
      <header>
        <h1 itemprop="headline">{post['title']}</h1>
        {labels_html}
        <meta itemprop="datePublished" content="{published_date}">
        <meta itemprop="dateModified" content="{updated_date}">
        <div itemprop="author" itemscope itemtype="http://schema.org/Person">
          <meta itemprop="name" content="Nama Penulis Anda"> </div>
        <div itemprop="publisher" itemscope itemtype="http://schema.org/Organization">
          <meta itemprop="name" content="Cerita Seks Dewasa">
          <meta itemprop="logo" content="{BASE_URL}assets/logo.png"> </div>
        <meta itemprop="image" content="{thumbnail_url}">
      </header>
      <div itemprop="articleBody">{post['content']}</div>
    </article>
    <aside>{SIDEBAR_HTML}</aside>
  </main>
  {FOOTER_HTML}
</body>
</html>""")
    print(f"  ✅ Artikel '{post['title']}' digenerate: {filepath}")
    return filename

def generate_index_pages(posts):
    """
    Membuat halaman indeks (beranda) dan halaman paginasi.
    Memastikan URL yang bersih dan meta tag yang relevan.
    """
    total_pages = (len(posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE
    print(f"\nMemulai generasi halaman indeks ({total_pages} halaman)...")
    for i in range(total_pages):
        page_posts = posts[i*POSTS_PER_PAGE:(i+1)*POSTS_PER_PAGE]
        fname = "index.html" if i == 0 else f"page{i+1}.html"
        
        page_title = "Cerita Seks Dewasa" if i == 0 else f"Cerita Seks Dewasa - Halaman {i+1}"
        page_description = "Kumpulan cerita seks dewasa terbaru dan terpopuler. Baca cerita-cerita menarik dan seru di sini." if i == 0 else f"Halaman {i+1} dari kumpulan cerita seks dewasa. Lanjutkan membaca."
        
        # Canonical URL untuk halaman indeks dan paginasi
        canonical_url = f"{BASE_URL}{fname}"

        with open(fname, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <meta name="description" content="{page_description}">
  <link rel="canonical" href="{canonical_url}">
  <link rel="stylesheet" href="assets/style.css">
  
  <meta property="og:title" content="{page_title}">
  <meta property="og:description" content="{page_description}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:image" content="{BASE_URL}assets/og-image.jpg"> {HEAD_HTML}
</head>
<body>
  {HEADER_HTML}
  <main>
    <section>""")
            for post in page_posts:
                post_file = generate_post_page(post) # Panggil fungsi generate_post_page di sini
                snippet = strip_html(post['content'])
                # Batasi snippet agar tidak terlalu panjang di halaman indeks
                display_snippet = (snippet[:200] + '...') if len(snippet) > 200 else snippet
                thumb = extract_thumbnail(post['content'], post['title']) # Pass title to extract_thumbnail
                labels = render_labels(post.get("labels", []))
                
                f.write(f"""
      <article>
        <a href="posts/{post_file}">
          <img class="thumbnail" src="{thumb}" alt="{post['title']}">
          <h2>{post['title']}</h2>
        </a>
        {labels}
        <p>{display_snippet} <a href="posts/{post_file}">Baca selengkapnya</a></p>
      </article>""")

            f.write("</section><aside>{}</aside></main><nav class='pagination'>".format(SIDEBAR_HTML))
            
            # Navigasi paginasi dengan rel="prev" dan rel="next"
            if i > 0:
                prev_page_name = "index.html" if i == 0 else f"page{i}.html"
                f.write(f"<a href='{prev_page_name}' rel='prev'>&laquo; Sebelumnya</a>")

            for j in range(total_pages):
                page_name = "index.html" if j == 0 else f"page{j+1}.html"
                active = "class='active'" if j == i else ""
                f.write(f"<a href='{page_name}' {active}>{j+1}</a>")
            
            if i < total_pages - 1:
                next_page_name = f"page{i+2}.html"
                f.write(f"<a href='{next_page_name}' rel='next'>Selanjutnya &raquo;</a>")

            f.write(f"</nav>{FOOTER_HTML}</body></html>")
        print(f"  ✅ Halaman indeks digenerate: {fname}")

def generate_label_pages(posts):
    """
    Membuat halaman untuk setiap kategori (label).
    Memastikan URL yang bersih dan meta tag yang relevan untuk halaman kategori.
    """
    label_map = {}
    for post in posts:
        for label in post.get("labels", []):
            label_map.setdefault(label, []).append(post)

    print("\nMemulai generasi halaman kategori (label)...")
    for label, items in label_map.items():
        fname = f"labels/{sanitize(label)}.html"
        
        label_title = f"Kategori: {label} | Cerita Seks Dewasa"
        label_description = f"Temukan semua cerita di kategori {label} di Cerita Seks Dewasa."
        label_url = f"{BASE_URL}{fname}"

        with open(fname, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{label_title}</title>
  <meta name="description" content="{label_description}">
  <link rel="canonical" href="{label_url}">
  <link rel="stylesheet" href="../assets/style.css">
  
  <meta property="og:title" content="{label_title}">
  <meta property="og:description" content="{label_description}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{label_url}">
  <meta property="og:image" content="{BASE_URL}assets/og-image.jpg">
  
  {HEAD_HTML}
</head>
<body>
  {HEADER_HTML}
  <main>
    <section><h1>Kategori: {label}</h1>""")
            for post in items:
                # Perhatikan: post_file sudah digenerate sebelumnya di generate_index_pages
                # atau akan digenerate di sini jika halaman kategori diakses langsung
                # Untuk menghindari generasi berulang, pastikan generate_post_page dipanggil sekali per post
                post_file_name = f"{sanitize(post['title'])}-{post['id']}.html"
                
                snippet = strip_html(post['content'])
                display_snippet = (snippet[:200] + '...') if len(snippet) > 200 else snippet
                thumb = extract_thumbnail(post['content'], post['title'])
                
                f.write(f"""
      <article>
        <a href="../posts/{post_file_name}">
          <img class="thumbnail" src="{thumb}" alt="{post['title']}">
          <h2>{post['title']}</h2>
        </a>
        <p>{display_snippet} <a href="../posts/{post_file_name}">Baca selengkapnya</a></p>
      </article>""")
            f.write(f"</section><aside>{SIDEBAR_HTML}</aside></main>{FOOTER_HTML}</body></html>")
        print(f"  ✅ Halaman kategori digenerate: {fname}")

# --- Eksekusi Utama ---
if __name__ == '__main__':
    try:
        posts = fetch_all_posts()
        # Urutkan postingan berdasarkan tanggal terbaru (misalnya, 'updated' atau 'published')
        # Ini penting untuk konsistensi dan menunjukkan konten segar.
        posts.sort(key=lambda x: x.get('updated', x.get('published', '')), reverse=True)
        
        generate_index_pages(posts)
        generate_label_pages(posts)
        print(f"\n✅ Proses selesai. Total {len(posts)} artikel berhasil digenerate.")
    except Exception as e:
        print(f"❌ Terjadi kesalahan: {e}")
