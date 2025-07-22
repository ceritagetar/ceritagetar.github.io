# src/build.py
import os
import shutil
import requests # Library untuk membuat permintaan HTTP ke API
import json     # Library untuk mengolah data JSON

# --- Konfigurasi ---
OUTPUT_DIR = "dist"              # Nama folder output untuk file statis
ASSETS_SOURCE_DIR = "src/assets" # Lokasi aset statis seperti CSS

# --- Mengambil API Key dan Blog ID dari Variabel Lingkungan ---
# GitHub Actions akan menyetel variabel lingkungan ini dari GitHub Secrets Anda.
BLOGGER_API_KEY = os.getenv('AIzaSyBglonTK3lbLZwqYKSuI3Vj64HUbdPWq6s')
BLOG_ID = os.getenv('8601707668889540603')

# --- Pengecekan Awal: Memastikan Kunci dan ID Tersedia ---
if not BLOGGER_API_KEY or not BLOG_ID:
    print("Error: BLOGGER_API_KEY atau BLOG_ID tidak ditemukan di variabel lingkungan.")
    print("Pastikan Anda telah menyetelnya sebagai GitHub Secrets di repositori Anda.")
    # Keluar dari skrip dengan kode error jika variabel tidak ada
    exit(1)

# --- Fungsi untuk Mengambil Data dari Blogger API ---
def fetch_blogger_data():
    """
    Mengambil daftar postingan dari Blogger API menggunakan BLOG_ID dan BLOGGER_API_KEY.
    """
    print("➡️ Mengambil data dari Blogger API...")
    # URL dasar untuk Blogger API v3 posts list
    # Anda bisa menambahkan parameter lain seperti 'maxResults', 'fields', dll.
    api_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts?key={BLOGGER_API_KEY}"

    try:
        response = requests.get(api_url)
        # Memunculkan HTTPError untuk status kode error (4xx atau 5xx)
        response.raise_for_status()
        data = response.json()
        posts = data.get('items', []) # Mengambil daftar postingan
        print(f"✅ Berhasil mengambil {len(posts)} postingan dari Blogger API.")
        return posts
    except requests.exceptions.RequestException as e:
        print(f"❌ Error saat mengambil data dari Blogger API: {e}")
        return [] # Kembalikan list kosong jika ada error

# --- Fungsi untuk Menghasilkan Konten HTML ---
def generate_html_content(posts_data):
    """
    Membuat string HTML lengkap berdasarkan data postingan yang diterima dari Blogger API.
    """
    html_template_start = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog Dinamis dari Blogger API</title>
    <link rel="stylesheet" href="style.css">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        header { background: #f4f4f4; padding: 10px 0; text-align: center; }
        main { max-width: 800px; margin: 20px auto; padding: 0 15px; }
        article { border-bottom: 1px solid #eee; padding-bottom: 20px; margin-bottom: 20px; }
        article:last-child { border-bottom: none; }
        h1, h2 { color: #333; }
        p { color: #666; }
        .post-meta { font-size: 0.9em; color: #888; margin-top: -10px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <header>
        <h1>My Dynamic Blog</h1>
        <p>Powered by Blogger API and GitHub Actions!</p>
    </header>
    <main>
"""
    posts_html_parts = []
    if not posts_data:
        posts_html_parts.append("<p>Tidak ada postingan yang ditemukan.</p>")
    else:
        for post in posts_data:
            title = post.get('title', 'Judul Tidak Tersedia')
            # Konten dari Blogger API bisa berupa HTML, jadi kita langsung masukkan
            content = post.get('content', 'Konten Tidak Tersedia')
            published_date = post.get('published', 'Tanggal Tidak Tersedia')

            posts_html_parts.append(f"""
        <article>
            <h2>{title}</h2>
            <p class="post-meta">Dipublikasikan: {published_date}</p>
            <div class="post-content">{content}</div>
        </article>
""")

    html_template_end = """
    </main>
    <footer>
        <p>&copy; 2025 Blog Dinamis. Semua hak dilindungi undang-undang.</p>
    </footer>
</body>
</html>
"""
    return html_template_start + "\n".join(posts_html_parts) + html_template_end

# --- Main Logic dari Skrip ---
if __name__ == "__main__":
    print(f"🚀 Memulai proses build ke direktori: {OUTPUT_DIR}")

    # 1. Persiapan Direktori Output ('dist')
    # Hapus folder 'dist' jika sudah ada untuk memastikan build yang bersih
    if os.path.exists(OUTPUT_DIR):
        print(f"🗑️ Menghapus direktori lama: {OUTPUT_DIR}")
        shutil.rmtree(OUTPUT_DIR)

    # Buat folder 'dist' yang baru
    print(f"✨ Membuat direktori baru: {OUTPUT_DIR}")
    os.makedirs(OUTPUT_DIR)

    # 2. Salin Aset Statis (misalnya, style.css)
    # Pastikan file src/assets/style.css Anda ada.
    style_css_src = os.path.join(ASSETS_SOURCE_DIR, "style.css")
    style_css_dest = os.path.join(OUTPUT_DIR, "style.css")
    if os.path.exists(style_css_src):
        print(f"📝 Menyalin '{style_css_src}' ke '{style_css_dest}'")
        shutil.copyfile(style_css_src, style_css_dest)
    else:
        print(f"⚠️ Peringatan: File '{style_css_src}' tidak ditemukan. Pastikan ada.")

    # 3. Ambil Data Postingan dari Blogger API
    posts = fetch_blogger_data()

    # 4. Hasilkan file HTML utama (index.html)
    output_html_content = generate_html_content(posts)
    output_html_path = os.path.join(OUTPUT_DIR, "index.html")
    print(f"✍️ Menulis HTML yang dihasilkan ke '{output_html_path}'")
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(output_html_content)

    print("✅ Proses build ke direktori 'dist' selesai!")
