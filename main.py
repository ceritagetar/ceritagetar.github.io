import os
import re
import math
from utils import get_secret, get_blogger_posts
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup
from datetime import datetime # Import datetime dengan benar

# --- Fungsi Pembantu ---
def slugify(text):
    """Mengubah teks menjadi slug yang valid untuk URL."""
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+', '', text)
    text = re.sub(r'-+$', '', text)
    return text

def parse_html_content_preview(html_content, num_words=30): # Default 30 kata untuk pratinjau
    """Mengambil beberapa kata pertama dari konten HTML sebagai pratinjau teks."""
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
    """
    Mengambil URL gambar pertama dari konten HTML dan mengoptimalkan ukurannya
    menggunakan parameter URL Blogger/Google Photos.
    Parameter 'size' bisa berupa 's<angka>' (lebar maks) atau 'w<lebar>-h<tinggi>'.
    """
    if not html_content:
        return None
    soup = BeautifulSoup(html_content, 'html.parser')
    first_img = soup.find('img')
    if first_img and 'src' in first_img.attrs:
        img_url = first_img['src']
        # Mengganti bagian ukuran di URL Blogger (misal: /s1600/ menjadi /s320/)
        # Pola regex mencari /s<angka>/ atau /w<angka>-h<angka>/
        optimized_url = re.sub(r'/(s\d+|w\d+-h\d+)/', f'/{size}/', img_url)
        return optimized_url
    return None

def optimize_blogger_images_in_content(html_content, default_size='s800'):
    """
    Memproses semua tag <img> dalam konten HTML:
    1. Mengubah ukuran gambar menggunakan parameter URL Blogger.
    2. Menambahkan atribut loading="lazy" untuk lazy loading.
    3. Menambahkan atribut alt jika belum ada.
    """
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, 'html.parser')
    for img_tag in soup.find_all('img'):
        if 'src' in img_tag.attrs:
            img_url = img_tag['src']
            # Mengganti bagian ukuran di URL Blogger
            optimized_url = re.sub(r'/(s\d+|w\d+-h\d+)/', f'/{default_size}/', img_url)
            img_tag['src'] = optimized_url
            
            # Tambahkan atribut loading="lazy"
            img_tag['loading'] = 'lazy' 
            
            # Tambahkan atribut alt jika belum ada atau kosong
            if not img_tag.get('alt', '').strip():
                # Bisa disesuaikan, misalnya mengambil bagian dari judul post
                img_tag['alt'] = 'Gambar Postingan' 
    return str(soup)

# --- Fungsi Utama ---
def main():
    try:
        blogger_api_key = get_secret("BLOGGER_API_KEY")
        blog_id = get_secret("BLOG_ID")

        print("Fetching ALL Blogger posts...")
        all_posts = []
        next_page_token = None
        while True:
            # Mengambil 500 postingan per request untuk mempercepat proses
            posts_data = get_blogger_posts(blog_id, blogger_api_key, max_results=500, page_token=next_page_token) 
            if posts_data and 'items' in posts_data:
                for post_item in posts_data['items']:
                    if 'content' in post_item:
                        all_posts.append(post_item)
                next_page_token = posts_data.get('nextPageToken')
                if not next_page_token:
                    break
            else:
                break
        
        if all_posts:
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
            # Filter date untuk menampilkan tahun di footer (digunakan di custom_footer.html)
            env.filters['date'] = lambda value, format="%Y": datetime.strptime(value, '%Y-%m-%dT%H:%M:%S%z').strftime(format) 

            base_template = env.get_template('base_template.html')
            
            processed_posts_for_template = []
            all_labels = set() 
            posts_by_label = {} 

            for post in all_posts:
                post_slug = slugify(post.get('title', 'untitled-post'))
                post_filename = f"{post_slug}.html"
                
                post['detail_url'] = f"/{post_filename}" 

                raw_html_content = post.get('content')
                
                post['thumbnail_url'] = get_first_image_url(raw_html_content, size='s320')
                post['parsed_content'] = parse_html_content_preview(raw_html_content, num_words=30) 
                
                post['optimized_content'] = optimize_blogger_images_in_content(raw_html_content, default_size='s800') 
                
                processed_posts_for_template.append(post)

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

                # --- Render Halaman Detail Postingan ---
                post_context = {
                    'post': post,
                    'all_labels': sorted(list(all_labels)) # Untuk sidebar di halaman detail
                }
                single_post_content = env.get_template('single_post_template.html').render(post_context)
                
                final_html = base_template.render(
                    content=single_post_content, 
                    title=post.get('title', 'Detail Postingan'), 
                    head_extra=f'<meta name="description" content="{post.get("parsed_content", "")}">', # Contoh meta description
                    all_labels=sorted(list(all_labels)) # Kirim ke base_template untuk sidebar
                )

                single_post_file_path = os.path.join(output_dir, post_filename)
                with open(single_post_file_path, "w", encoding="utf-8") as f:
                    f.write(final_html)
                print(f"Generated: {single_post_file_path}")
            
            # --- PAGINASI (Untuk index.html dan pages/*.html) ---
            posts_per_page = 5
            total_posts = len(processed_posts_for_template)
            total_pages = math.ceil(total_posts / posts_per_page)

            print(f"Total posts: {total_posts}, Posts per page: {posts_per_page}, Total pages: {total_pages}")

            for page_num in range(1, total_pages + 1):
                start_index = (page_num - 1) * posts_per_page
                end_index = start_index + posts_per_page
                current_page_posts = processed_posts_for_template[start_index:end_index]

                page_context = {
                    'posts': current_page_posts,
                    'current_page': page_num,
                    'total_pages': total_pages,
                    'all_labels': sorted(list(all_labels)) # Untuk sidebar
                }

                if page_num > 1:
                    page_context['prev_page_url'] = '/' if page_num == 2 else f'/pages/{page_num - 1}.html'
                else:
                    page_context['prev_page_url'] = None

                if page_num < total_pages:
                    page_context['next_page_url'] = f'/pages/{page_num + 1}.html'
                else:
                    page_context['next_page_url'] = None
                
                list_posts_content = env.get_template('index_template.html').render(page_context)
                
                page_title = 'Postingan Blog Saya'
                if page_num > 1:
                    page_title += f' - Halaman {page_num}'

                final_html = base_template.render(
                    content=list_posts_content,
                    title=page_title,
                    all_labels=sorted(list(all_labels)) # Kirim ke base_template untuk sidebar
                )

                if page_num == 1:
                    index_file_path = os.path.join(output_dir, 'index.html')
                    with open(index_file_path, "w", encoding="utf-8") as f:
                        f.write(final_html)
                    print(f"Generated: {index_file_path} (Page 1)")
                else:
                    page_filename = f"{page_num}.html"
                    page_file_path = os.path.join(pages_output_dir, page_filename)
                    with open(page_file_path, "w", encoding="utf-8") as f:
                        f.write(final_html)
                    print(f"Generated: {page_file_path} (Page {page_num})")
            
            # --- GENERASI HALAMAN DETAIL KATEGORI ---
            for label_slug, label_info in posts_by_label.items():
                category_detail_context = {
                    'label_name': label_info['name'],
                    'posts': label_info['posts'],
                    'all_labels': sorted(list(all_labels)) # Untuk sidebar
                }
                
                category_detail_content = env.get_template('category_detail_template.html').render(category_detail_context)
                
                final_html = base_template.render(
                    content=category_detail_content,
                    title=f"Kategori: {label_info['name']}",
                    all_labels=sorted(list(all_labels)) # Kirim ke base_template untuk sidebar
                )

                category_file_path = os.path.join(categories_output_dir, f"{label_slug}.html")
                with open(category_file_path, "w", encoding="utf-8") as f:
                    f.write(final_html)
                print(f"Generated: {category_file_path}")

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
