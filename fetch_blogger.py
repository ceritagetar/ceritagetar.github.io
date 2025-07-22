import requests
import os
import re
import json
import random
from html.parser import HTMLParser

# === Konfigurasi ===

API_KEY = os.environ.get('BLOGGER_API_KEY')
BLOG_ID = os.environ.get('BLOG_ID')

DIST_DIR = 'dist'
DATA_DIR = os.path.join(DIST_DIR, 'data')
POST_DIR = os.path.join(DIST_DIR, 'posts')
LABEL_DIR = os.path.join(DIST_DIR, 'labels')
POSTS_JSON = os.path.join(DATA_DIR, 'posts.json')
POSTS_PER_PAGE = 10

os.makedirs(DIST_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(LABEL_DIR, exist_ok=True)

# --- sisanya tetap seperti sebelumnya ---
# kamu bisa paste ulang seluruh kode dari bagian `class ImageExtractor(HTMLParser)` 
# sampai akhir tanpa perlu diubah,
# KECUALI bagian generate_index() dan generate_label_pages()
# yang diubah sedikit untuk menyimpan output ke dist/

# === Halaman index beranda ===

def generate_index(posts):
    total_pages = paginate(len(posts), POSTS_PER_PAGE)
    for page in range(1, total_pages + 1):
        start = (page - 1) * POSTS_PER_PAGE
        end = start + POSTS_PER_PAGE
        items = posts[start:end]
        items_html = ""
        for post in items:
            post_filename = generate_post_page(post, posts)
            post_absolute_link = f"/posts/{post_filename}"
            snippet = strip_html(post.get('content', ''))[:100]
            thumb = extract_thumbnail(post.get('content', ''))

            first_label_html = ""
            if post.get('labels'):
                label_name = post['labels'][0]
                sanitized_label_name = sanitize_filename(label_name)
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
        output_file = "index.html" if page == 1 else f"index-{page}.html"
        output_path = os.path.join(DIST_DIR, output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
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
                post_absolute_link = f"/posts/{post_filename}"
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
            output_file = f"{sanitize_filename(label)}-{page}.html"
            output_path = os.path.join(LABEL_DIR, output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

# === Eksekusi ===

if __name__ == '__main__':
    print("📥 Mengambil artikel...")
    posts = fetch_posts()
    print(f"✅ Artikel diambil: {len(posts)}")
    generate_index(posts)
    generate_label_pages(posts)
    print("✅ Halaman index, label, dan artikel selesai dibuat di folder dist/")
