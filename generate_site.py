# scripts/generate_site.py (Nama file Python yang diubah, contoh)
import requests
import os
import re
import json
import random
from html.parser import HTMLParser

# === Konfigurasi ===

API_KEY = os.environ.get('BLOGGER_API_KEY')
BLOG_ID = os.environ.get('BLOG_ID')

# --- PERUBAHAN UTAMA DI SINI ---
# Tentukan direktori output utama untuk semua file statis Anda
# Ini akan menjadi root situs yang di-deploy ke GitHub Pages
BUILD_OUTPUT_DIR = '_site' 

# Jalur relatif ke dalam BUILD_OUTPUT_DIR
DATA_DIR = os.path.join(BUILD_OUTPUT_DIR, 'data')
POST_DIR = os.path.join(BUILD_OUTPUT_DIR, 'posts') # Ini adalah folder tempat artikel akan disimpan
LABEL_DIR = os.path.join(BUILD_OUTPUT_DIR, 'labels')
POSTS_JSON = os.path.join(DATA_DIR, 'posts.json')
POSTS_PER_PAGE = 10

# Pastikan semua direktori dibuat di dalam BUILD_OUTPUT_DIR
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(LABEL_DIR, exist_ok=True)
# os.makedirs(BUILD_OUTPUT_DIR, exist_ok=True) # Ini sudah dicover oleh os.makedirs(DATA_DIR, exist_ok=True) dll.

# === Utilitas (Tidak perlu diubah) ===
# ... kode utilitas Anda (ImageExtractor, strip_html, remove_anchor_tags, sanitize_filename, render_labels, load_template, render_template, paginate, generate_pagination_links) tetap sama ...

# === Komponen Custom (Head, Header, Sidebar, Footer) ===
# Path ke file template kustom Anda harus relatif dari root repositori,
# BUKAN dari BUILD_OUTPUT_DIR, karena file-file ini ada di repo utama.
CUSTOM_HEAD_CONTENT = safe_load("custom_head.html")
CUSTOM_JS = safe_load("custom_js.html")
CUSTOM_HEADER = safe_load("custom_header.html")
CUSTOM_SIDEBAR = safe_load("custom_sidebar.html")
CUSTOM_FOOTER = safe_load("custom_footer.html")

CSS_FOR_RELATED_POSTS = """
# ... CSS Anda ...
"""

CSS_FOR_PAGE_NAVIGATION = """
# ... CSS Anda ...
"""

CUSTOM_HEAD_FULL = CUSTOM_HEAD_CONTENT + CSS_FOR_RELATED_POSTS + CSS_FOR_PAGE_NAVIGATION + CUSTOM_JS

# === Ambil semua postingan dari Blogger ===
# ... fetch_posts() tetap sama ...

# === Template ===
# Path ke file template HTML harus relatif dari root repositori Anda.
POST_TEMPLATE = load_template("post_template.html")
INDEX_TEMPLATE = load_template("index_template.html")
LABEL_TEMPLATE = load_template("label_template.html")

# === Halaman per postingan ===
def generate_post_page(post, all_posts):
    # Nama file artikel yang akan disimpan di dalam folder POST_DIR ('_site/posts/')
    filename_without_path = f"{sanitize_filename(post['title'])}.html"
    filepath = os.path.join(POST_DIR, filename_without_path) # Path lengkap untuk menyimpan file

    # Link absolut ke artikel tetap sama, karena relatif terhadap root situs yang di-deploy
    # Contoh: /posts/judul-artikel-terkait.html
    related_post_absolute_link_prefix = "/posts/" # Tetap "/posts/" untuk URL di browser
    post_absolute_link = f"{related_post_absolute_link_prefix}{filename_without_path}"

    # ... Sisa logika generate_post_page tetap sama, pastikan link absolut sudah benar ...

    # Mengembalikan hanya nama file untuk digunakan di tempat lain (misalnya index dan label pages)
    return filename_without_path

# === Halaman index beranda ===
def generate_index(posts):
    total_pages = paginate(len(posts), POSTS_PER_PAGE)
    for page in range(1, total_pages + 1):
        start = (page - 1) * POSTS_PER_PAGE
        end = start + POSTS_PER_PAGE
        items = posts[start:end]
        items_html = ""
        for post in items:
            # generate_post_page sekarang mengembalikan hanya nama file (tanpa path 'posts/')
            # Kita perlu tambahkan '/posts/' di depannya untuk link di index
            post_filename = generate_post_page(post, posts)
            post_absolute_link = f"/posts/{post_filename}" # Link absolut ke artikel

            snippet = strip_html(post.get('content', ''))[:100]
            thumb = extract_thumbnail(post.get('content', ''))

            first_label_html = ""
            if post.get('labels'):
                label_name = post['labels'][0]
                sanitized_label_name = sanitize_filename(label_name)
                # Link label juga perlu absolut
                first_label_html = f'<span class="label"><a href="/labels/{sanitized_label_name}-1.html">{label_name}</a></span>'

            items_html += f"""
<div class="post">
<div class="post-body">
<div class='label-line'>
    <span class='label-info-th'>{first_label_html}</span></div>
    <div class="img-thumbnail"><img src="{thumb}" alt=""></div>
    <h2 class="post-title"><a href="{post_absolute_link}">{post['title']}</a></h2>
    <p class="post-snippet">{snippet}... <a href="{post_absolute_link}">Baca selengkapnya</a></p>
    </div>
    </div>
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
        # --- PERUBAHAN DI SINI ---
        # Output file index juga harus masuk ke BUILD_OUTPUT_DIR
        output_file = os.path.join(BUILD_OUTPUT_DIR, f"index.html" if page == 1 else f"index-{page}.html")
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
                post_filename = generate_post_page(post, posts)
                post_absolute_link = f"/posts/{post_filename}" # Link absolut ke artikel

                snippet = strip_html(post.get('content', ''))[:150]
                thumb = extract_thumbnail(post.get('content', ''))
                items_html += f"""
<article id="post-wrapper">
  <a href="{post_absolute_link}">
    <img class="thumbnail" src="{thumb}" alt="">
    <h2>{post['title']}</h2>
  </a>
  <p>{snippet}... <a href="{post_absolute_link}">Baca selengkapnya</a></p>
</article>
"""
            pagination = generate_pagination_links(
                f"labels/{sanitize_filename(label)}", page, total_pages
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
            # --- PERUBAHAN DI SINI ---
            # Output file label juga harus masuk ke BUILD_OUTPUT_DIR/labels/
            output_file = os.path.join(LABEL_DIR, f"{sanitize_filename(label)}-{page}.html")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

# === Eksekusi ===
if __name__ == '__main__':
    # Pastikan direktori _site dibuat sebelum skrip mulai menulis file
    os.makedirs(BUILD_OUTPUT_DIR, exist_ok=True) 

    print("📥 Mengambil artikel...")
    posts = fetch_posts()
    print(f"✅ Artikel diambil: {len(posts)}")
    
    # generate_post_page dipanggil di dalam generate_index dan generate_label_pages,
    # jadi tidak perlu dipanggil di sini lagi secara eksplisit untuk setiap post.
    # Namun, Anda perlu memindahkan `os.makedirs(POST_DIR, exist_ok=True)` ke atas
    # di bagian konfigurasi agar folder `_site/posts` siap saat dibutuhkan.
    
    generate_index(posts)
    generate_label_pages(posts)
    print("✅ Halaman index, label, dan artikel selesai dibuat di folder _site.")
