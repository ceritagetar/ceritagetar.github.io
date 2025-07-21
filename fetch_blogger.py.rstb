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
POST_DIR = 'posts' # Ini adalah folder tempat artikel akan disimpan
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
    return parser.thumbnail or 'https://placehold.co/100x56.25/E0E0E0/333333?text=No+Image'

def strip_html(html):
    return re.sub('<[^<]+?>', '', html)

def remove_anchor_tags(html_content):
    return re.sub(r'<a[^>]*>(.*?)<\/a>', r'\1', html_content)

def sanitize_filename(title):
    # Membersihkan judul untuk digunakan sebagai nama file
    return re.sub(r'\W+', '-', title.lower()).strip('-')

def render_labels(labels):
    if not labels:
        return ""
    html = '<div class="labels">'
    for label in labels:
        filename = sanitize_filename(label)
        # Link label juga perlu diperbaiki jika ingin absolut
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
    # Start the main pagination container with the #blog-pager ID
    html = '<div id="blog-pager">'

    # Newer Post Link (Previous Page)
    if current > 1:
        prev_page_suffix = "" if current - 1 == 1 and "index" in base_url else f"-{current - 1}"
        prev_page_full_url = f"/{base_url}{prev_page_suffix}.html"
        html += f'<div id="blog-pager-newer-link"><a href="{prev_page_full_url}">Newer Post</a></div>'

    # Generate numbered page links
    # This section needs to align with the CSS's .displaypageNum a and .pagecurrent
    html += '<span class="pages">' # Container for page numbers

    def page_link_html(page_num, is_current):
        suffix = "" if page_num == 1 and "index" in base_url else f"-{page_num}"
        full_url = f"/{base_url}{suffix}.html"
        if is_current:
            # Apply pagecurrent class to the span for the current page
            return f'<span class="pagecurrent"><a href="{full_url}">{page_num}</a></span>'
        else:
            # Apply displaypageNum to other pages, which will target the <a> inside
            return f'<span class="displaypageNum"><a href="{full_url}">{page_num}</a></span>'


    # Logic for displaying a range of pages (simplified for brevity, can be expanded)
    # The original logic for `total <= 10` and `else` (with ellipsis) is maintained
    # but the `page_link` function is replaced by `page_link_html` which applies correct classes.
    if total <= 10:
        for i in range(1, total + 1):
            html += page_link_html(i, i == current)
    else:
        # First few pages
        for i in range(1, min(total + 1, 4)): # Up to page 3
            html += page_link_html(i, i == current)

        # Ellipsis if current page is far from the beginning
        if current > 5 and total > 6:
            html += '<span>...</span>'

        # Current page and its immediate neighbors
        start_middle = max(4, current - 1)
        end_middle = min(total - 2, current + 1)
        if current >= 4 and current <= total - 3:
             for i in range(start_middle, end_middle + 1):
                 if i > 3 and i < total - 1: # Avoid re-printing pages already covered or last few
                     html += page_link_html(i, i == current)

        # Ellipsis if current page is far from the end
        if current < total - 4 and total > 6:
            html += '<span>...</span>'
        
        # Last few pages
        for i in range(max(total - 1, 4), total + 1): # From page (total-1) to total
            if i > 3: # Ensure we don't duplicate pages already covered by initial range
                html += page_link_html(i, i == current)

    html += '</span>' # Close span class="pages"


    # Older Post Link (Next Page)
    if current < total:
        next_page_suffix = f"-{current + 1}"
        next_page_full_url = f"/{base_url}{next_page_suffix}.html"
        html += f'<div id="blog-pager-older-link"><a href="{next_page_full_url}">Older Post</a></div>'
    
    # Close the main pagination container
    html += '<div style="clear:both;"></div>' # Clear floats within blog-pager, though CSS has clear:both !important on #blog-pager itself
    html += '</div>'
    return html

# === Komponen Custom (Head, Header, Sidebar, Footer) ===

def safe_load(path):
    return load_template(path) if os.path.exists(path) else ""

CSS_FOR_RELATED_POSTS = """
<style>
/* Popular Posts */
.PopularPosts .widget-content ul, .PopularPosts .widget-content ul li, .PopularPosts .widget-content ul li img, .PopularPosts .widget-content ul li a, .PopularPosts .widget-content ul li a img {
    margin:0 0;
    padding:0 0;
    list-style:none;
    border:none;
    outline:none;
}
.PopularPosts .widget-content ul {
    margin: 0;
    list-style:none;
}
.PopularPosts .widget-content ul li img {
    display: block;
    width: 100px;
    height: 56.25px;
    float: left;
    border-radius: 3px;
}
.PopularPosts .widget-content ul li img:hover { opacity: 0.8;
transform: scale(1.05);
}

.PopularPosts .widget-content ul li {
    margin: 10px 0px;
    position: relative;
    overflow: hidden; /* Untuk membersihkan float di dalam li */
}
.PopularPosts ul li:last-child {
    margin-bottom: 5px;
}
.PopularPosts ul li .item-title a, .PopularPosts ul li a {
    font-weight: 700;
    text-decoration: none;
    font-size: 14px;
}
.PopularPosts ul li .item-title a:hover, .PopularPosts ul li a:hover {
    color: #595959;
}

.PopularPosts .item-title, .PopularPosts .item-snippet {
    margin-left: 110px; /* Jarak dari gambar thumbnail */
}
.PopularPosts .item-title {
    line-height: 1.6;
    margin-right: 8px;
}
.PopularPosts .item-thumbnail {
    float: left;
}
</style>
"""

# New CSS for Page Navigation
CSS_FOR_PAGE_NAVIGATION = """
<style>
/* PAGE NAVIGATION */
#blog-pager {
    clear:both !important;
    padding:2px 0;
    text-align: center;
}
#blog-pager-newer-link a {
    float:left;
    display:block;
}
#blog-pager-older-link a {
    float:right;
    display:block;
}
.displaypageNum a,.showpage a,.pagecurrent, #blog-pager-newer-link a, #blog-pager-older-link a {
    font-size: 14px;
    padding: 8px 12px;
    margin: 2px 3px 2px 0px;
    display: inline-block;
    color: #1b699d;
    background: rgba(195, 195, 195, 0.15);
    text-decoration: none; /* Ensure links are not underlined by default */
    border-radius: 4px; /* Added for better aesthetics */
    transition: all 0.3s ease; /* Smooth transition for hover effects */
}
#blog-pager-older-link a:hover, #blog-pager-newer-link a:hover, a.home-link:hover, .displaypageNum a:hover,.showpage a:hover, .pagecurrent {
    color: #ffffff; /* Example: White text on hover/active */
    background: #1b699d; /* Example: Blue background on hover/active */
    /* Note: $(link.hover.color) is a Blogger variable, replaced with a placeholder */
}
.showpageOf { 
    display: none !important;
}
#blog-pager .pages {
    border: none;
    display: inline-block; /* To center the page numbers */
}
#blog-pager .pages .pagecurrent a, #blog-pager .pages .displaypageNum a {
    /* Ensure internal page links get the same base styling */
    color: #1b699d;
    background: rgba(195, 195, 195, 0.15);
}
#blog-pager .pages .pagecurrent {
    /* Style for the current page container, overriding base link style if needed */
    color: #ffffff;
    background: #1b699d;
    font-weight: bold;
    border-radius: 4px;
}
</style>
"""

CUSTOM_HEAD_CONTENT = safe_load("custom_head.html")
CUSTOM_JS = safe_load("custom_js.html")
CUSTOM_HEADER = safe_load("custom_header.html")
CUSTOM_SIDEBAR = safe_load("custom_sidebar.html")
CUSTOM_FOOTER = safe_load("custom_footer.html")

CUSTOM_HEAD_FULL = CUSTOM_HEAD_CONTENT + CSS_FOR_RELATED_POSTS + CSS_FOR_PAGE_NAVIGATION + CUSTOM_JS

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
    # Nama file artikel yang akan disimpan di dalam folder POST_DIR ('posts/')
    filename_without_path = f"{sanitize_filename(post['title'])}.html"
    filepath = os.path.join(POST_DIR, filename_without_path) # Path lengkap untuk menyimpan file

    # Filter postingan yang memiliki konten sebelum sampling
    eligible_related = [p for p in all_posts if p['id'] != post['id'] and 'content' in p]
    related_sample = random.sample(eligible_related, min(5, len(eligible_related)))

    related_items_html = []
    for p_related in related_sample:
        # Link untuk artikel terkait, gunakan path absolut dari root situs
        # Contoh: /posts/judul-artikel-terkait.html
        related_post_absolute_link = f"/posts/{sanitize_filename(p_related['title'])}.html"
        
        related_post_content = p_related.get('content', '')
        thumb = extract_thumbnail(related_post_content)
        snippet = strip_html(related_post_content)
        snippet = snippet[:100] + "..." if len(snippet) > 100 else snippet

        related_items_html.append(f"""
            <li>
                <a href="{related_post_absolute_link}">
                    <img class="item-thumbnail" src="{thumb}" alt="{p_related["title"]}">
                </a>
                <div class="item-title"><a href="{related_post_absolute_link}">{p_related["title"]}</a></div>
                <div class="item-snippet">{snippet}</div>
            </li>
        """)
    
    related_html = f"""
    <div class="PopularPosts">
        <div class="widget-content">
            <ul>
                {"".join(related_items_html)}
            </ul>
        </div>
    </div>
    """

    processed_content = remove_anchor_tags(post.get('content', ''))

    html = render_template(POST_TEMPLATE,
        title=post['title'],
        content=processed_content,
        labels=render_labels(post.get("labels", [])),
        related=related_html,
        custom_head=CUSTOM_HEAD_FULL,
        custom_header=CUSTOM_HEADER,
        custom_sidebar=CUSTOM_SIDEBAR,
        custom_footer=CUSTOM_FOOTER
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    # Mengembalikan hanya nama file untuk digunakan di tempat lain (misalnya index dan label pages)
    # Ini akan digabungkan dengan /posts/ di fungsi pemanggil
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
                # generate_post_page mengembalikan nama file saja
                # Kita perlu tambahkan '/posts/' di depannya untuk link di halaman label
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
