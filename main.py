import os
import re
import math
from utils import get_secret, get_blogger_posts
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup
from datetime import datetime
# Import dateutil jika kamu memilih opsi parser.parse
# from dateutil import parser # <-- Hapus komentar ini jika ingin pakai dateutil

# --- Fungsi Pembantu (Sama seperti sebelumnya) ---
def slugify(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+', '', text)
    text = re.sub(r'-+$', '', text)
    return text

def parse_html_content_preview(html_content, num_words=30):
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    words = text.split()
    truncated_words = words[:num_words]
    preview_text = " ".join(truncated_words)
    if len(words) > num_words:
        preview_text += "..."
    return preview_text

def get_first_image_url(html_content, size='s320'):
    if not html_content:
        return None
    soup = BeautifulSoup(html_content, 'html.parser')
    first_img = soup.find('img')
    if first_img and 'src' in first_img.attrs:
        img_url = first_img['src']
        optimized_url = re.sub(r'/(s\d+|w\d+-h\d+)/', f'/{size}/', img_url)
        return optimized_url
    return None

def optimize_blogger_images_in_content(html_content, default_size='s800'):
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, 'html.parser')
    for img_tag in soup.find_all('img'):
        if 'src' in img_tag.attrs:
            img_url = img_tag['src']
            optimized_url = re.sub(r'/(s\d+|w\d+-h\d+)/', f'/{default_size}/', img_url)
            img_tag['src'] = optimized_url
            img_tag['loading'] = 'lazy'  
            if not img_tag.get('alt', '').strip():
                img_tag['alt'] = 'Gambar Postingan'  
    return str(soup)

# --- Fungsi Utama ---
def main():
    try:
        blogger_api_key = get_secret("BLOGGER_API_KEY")
        blog_id = get_secret("BLOG_ID")

        print("Fetching ALL Blogger posts...")
        all_posts_raw = [] # Mengubah nama variabel agar lebih jelas
        next_page_token = None
        while True:
            posts_data = get_blogger_posts(blog_id, blogger_api_key, max_results=500, page_token=next_page_token)  
            if posts_data and 'items' in posts_data:
                for post_item in posts_data['items']:
                    if 'content' in post_item:
                        all_posts_raw.append(post_item)
                next_page_token = posts_data.get('nextPageToken')
                if not next_page_token:
                    break
            else:
                break
        
        if all_posts_raw: # Menggunakan all_posts_raw
            output_dir = os.getcwd()  
            os.makedirs(output_dir, exist_ok=True)  
            print(f"Output directory created/ensured: {output_dir}")

            pages_output_dir = os.path.join(output_dir, 'pages')
            os.makedirs(pages_output_dir, exist_ok=True)
            print(f"Pages directory created/ensured: {pages_output_dir}")

            categories_output_dir = os.path.join(output_dir, 'kategori')
            os.makedirs(categories_output_dir, exist_ok=True)
            print(f"Categories directory created/ensured: {categories_output_dir}")

            template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
            if not os.path.isdir(template_dir):
                raise FileNotFoundError(f"Template directory not found: {template_dir}")
            
            template_loader = FileSystemLoader(template_dir)
            env = Environment(loader=template_loader)
            
            env.filters['slugify'] = slugify
            
            # Filter baru untuk mengonversi tanggal, asumsikan 'published' format ISO 8601
            # Contoh: "2023-10-27T10:00:00Z"
            env.filters['date_format'] = lambda value, fmt="%d %b %Y": datetime.fromisoformat(value.replace('Z', '+00:00')).strftime(fmt)
            
            list_posts_template = env.get_template('index_template.html')  
            single_post_template = env.get_template('single_post_template.html')
            category_detail_template = env.get_template('category_detail_template.html')

            # --- PRE-PROCESS SEMUA POSTINGAN UNTUK MEMBANGUN DATA YANG DIBUTUHKAN ---
            fully_processed_posts = []
            all_labels = set()  
            posts_by_label = {}  

            for post_item in all_posts_raw:
                post = post_item.copy()  

                post_slug = slugify(post.get('title', 'untitled-post'))
                # Gunakan 'id' atau 'url' dari Blogger jika ada untuk detail_url yang lebih stabil
                # Atau tetap pakai slug jika Anda ingin URL statis
                # post['detail_url'] = post.get('url') # Jika ingin pakai URL asli Blogger
                post['detail_url'] = f"/{post_slug}.html" # Jika ingin pakai slug sebagai URL file lokal
                
                raw_html_content = post.get('content', '')
                post['thumbnail_url'] = get_first_image_url(raw_html_content, size='s320')
                post['parsed_content'] = parse_html_content_preview(raw_html_content, num_words=13)  
                post['optimized_content'] = optimize_blogger_images_in_content(raw_html_content, default_size='s800')  
                
                # Pastikan tanggal 'published' ada dan valid untuk sorting
                if 'published' in post:
                    fully_processed_posts.append(post)

                labels = post.get('labels', [])
                if labels:
                    for label in labels:
                        all_labels.add(label)
                        label_slug = slugify(label)
                        if label_slug not in posts_by_label:
                            posts_by_label[label_slug] = {
                                'name': label,
                                'slug': label_slug,
                                'posts': []
                            }
                        posts_by_label[label_slug]['posts'].append(post)

            # --- BARIS BARU UNTUK MENGURUTKAN DAN MENGAMBIL POSTINGAN TERBARU ---
            # Urutkan semua postingan berdasarkan tanggal publikasi (terbaru dulu)
            # Pastikan 'published' ada di setiap post sebelum sorting
            fully_processed_posts.sort(key=lambda p: datetime.fromisoformat(p['published'].replace('Z', '+00:00')), reverse=True)
            
            # Ambil 5 postingan terbaru (Anda bisa ubah angka ini)
            num_recent_posts_widget = 5
            recent_posts_for_widget = fully_processed_posts[:num_recent_posts_widget]
            print(f"Collected {len(recent_posts_for_widget)} recent posts for the widget.")
            # --- AKHIR BARIS BARU ---


            # --- GENERASI HALAMAN INDIVIDUAL POSTINGAN & MENCARI RELATED POSTS ---
            for post in fully_processed_posts:  # Gunakan fully_processed_posts yang sudah diurutkan
                post_slug = slugify(post.get('title', 'untitled-post'))
                post_filename = f"{post_slug}.html"

                related_posts = []
                current_post_labels = set(post.get('labels', []))
                
                if current_post_labels:  
                    for other_post in fully_processed_posts:
                        if other_post['id'] != post['id'] and \
                           len(set(other_post.get('labels', [])) & current_post_labels) > 0:
                            related_posts.append(other_post)
                            
                        if len(related_posts) >= 5:  
                            break
                    
                post['related_posts'] = related_posts

                single_post_html = single_post_template.render(
                    post=post,
                    all_labels=sorted(list(all_labels)),  
                    current_year=datetime.now().year,
                    # --- TERUSKAN RECENT_POSTS KE SINGLE_POST_TEMPLATE JUGA ---
                    recent_posts=recent_posts_for_widget 
                )
                
                single_post_file_path = os.path.join(output_dir, post_filename)
                with open(single_post_file_path, "w", encoding="utf-8") as f:
                    f.write(single_post_html)
                print(f"Generated: {single_post_file_path}")
            
            # --- PAGINASI UNTUK HALAMAN UTAMA (index.html dan pages/*.html) ---
            posts_per_page = 5 # Jumlah postingan per halaman INDEX utama
            total_posts = len(fully_processed_posts)
            total_pages = math.ceil(total_posts / posts_per_page)

            print(f"Total posts: {total_posts}, Posts per page (Index): {posts_per_page}, Total pages (Index): {total_pages}")

            for page_num in range(1, total_pages + 1):
                start_index = (page_num - 1) * posts_per_page
                end_index = start_index + posts_per_page
                current_page_posts = fully_processed_posts[start_index:end_index]

                page_context = {
                    'posts': current_page_posts,
                    'current_page': page_num,
                    'total_pages': total_pages,
                    'all_labels': sorted(list(all_labels)),  
                    'current_year': datetime.now().year,
                    # --- TERUSKAN RECENT_POSTS KE INDEX_TEMPLATE (dan pages/*.html) ---
                    'recent_posts': recent_posts_for_widget 
                }

                if page_num > 1:
                    page_context['prev_page_url'] = '/' if page_num == 2 else f'/pages/{page_num - 1}.html'
                else:
                    page_context['prev_page_url'] = None

                if page_num < total_pages:
                    page_context['next_page_url'] = f'/pages/{page_num + 1}.html'
                else:
                    page_context['next_page_url'] = None
                
                rendered_page_html = list_posts_template.render(page_context)
                
                if page_num == 1:
                    index_file_path = os.path.join(output_dir, 'index.html')
                    with open(index_file_path, "w", encoding="utf-8") as f:
                        f.write(rendered_page_html)
                    print(f"Generated: {index_file_path} (Page 1)")
                else:
                    page_filename = f"{page_num}.html"
                    page_file_path = os.path.join(pages_output_dir, page_filename)
                    with open(page_file_path, "w", encoding="utf-8") as f:
                        f.write(rendered_page_html)
                    print(f"Generated: {page_file_path} (Page {page_num})")
            
            # --- GENERASI HALAMAN DETAIL KATEGORI (DENGAN PAGINASI UNTUK TIAP KATEGORI) ---
            posts_per_category_page = 5 # Jumlah postingan per halaman KATEGORI

            for label_slug, label_info in posts_by_label.items():
                # Pastikan postingan di kategori juga diurutkan berdasarkan tanggal terbaru
                category_posts = sorted(label_info['posts'], key=lambda p: datetime.fromisoformat(p['published'].replace('Z', '+00:00')), reverse=True)
                total_category_posts = len(category_posts)
                total_category_pages = math.ceil(total_category_posts / posts_per_category_page)

                print(f"Generating pages for category '{label_info['name']}': Total posts {total_category_posts}, Total pages {total_category_pages}")

                # Buat folder untuk sub-paginasi kategori jika diperlukan (misal: kategori/nama-slug/page/)
                category_slug_dir = os.path.join(categories_output_dir, label_slug)
                os.makedirs(category_slug_dir, exist_ok=True)


                for page_num in range(1, total_category_pages + 1):
                    start_index = (page_num - 1) * posts_per_category_page
                    end_index = start_index + posts_per_category_page
                    current_category_page_posts = category_posts[start_index:end_index]

                    # Konteks untuk template kategori
                    category_detail_context = {
                        'label_name': label_info['name'],
                        'label_slug': label_slug, # Tambahkan label_slug ke konteks agar bisa dipakai di template
                        'posts': current_category_page_posts,
                        'current_page': page_num,
                        'total_pages': total_category_pages,
                        'all_labels': sorted(list(all_labels)),
                        'current_year': datetime.now().year,
                        # --- TERUSKAN RECENT_POSTS KE CATEGORY_DETAIL_TEMPLATE JUGA ---
                        'recent_posts': recent_posts_for_widget 
                    }

                    # Atur URL paginasi untuk kategori
                    if page_num > 1:
                        # Link "Prev" akan mengarah ke root kategori jika ini halaman 2 (misal: /kategori/teknologi.html)
                        # atau ke subfolder 'page/X.html' jika halaman > 2 (misal: /kategori/teknologi/page/2.html)
                        category_detail_context['prev_page_url'] = \
                            f'/kategori/{label_slug}.html' if page_num == 2 else f'/kategori/{label_slug}/page/{page_num - 1}.html'
                    else:
                        category_detail_context['prev_page_url'] = None

                    if page_num < total_category_pages:
                        category_detail_context['next_page_url'] = f'/kategori/{label_slug}/page/{page_num + 1}.html'
                    else:
                        category_detail_context['next_page_url'] = None
                    
                    # Render HTML kategori
                    category_detail_html = category_detail_template.render(category_detail_context)
                    
                    # Tentukan path file output
                    if page_num == 1:
                        # Halaman pertama kategori akan disimpan di kategori/nama-slug.html
                        category_file_path = os.path.join(categories_output_dir, f"{label_slug}.html")
                    else:
                        # Halaman paginasi kategori akan disimpan di kategori/nama-slug/page/X.html
                        # Pastikan folder 'page' dibuat jika belum ada
                        category_page_dir = os.path.join(category_slug_dir, 'page')
                        os.makedirs(category_page_dir, exist_ok=True)
                        category_file_path = os.path.join(category_page_dir, f"{page_num}.html")
                    
                    with open(category_file_path, "w", encoding="utf-8") as f:
                        f.write(category_detail_html)
                    print(f"Generated: {category_file_path} (Category '{label_info['name']}' Page {page_num})")

        else:
            print("No posts found or an error occurred. No HTML files generated.")

    except FileNotFoundError as e:
        print(f"Error: {e}. Make sure 'templates' folder and template files exist in the correct location.")
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
