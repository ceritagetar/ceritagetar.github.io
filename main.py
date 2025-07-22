# main.py
import os
import re # Impor modul re untuk regex
from utils import get_secret, get_blogger_posts
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup

def slugify(text):
    """
    Converts text to a URL-friendly slug.
    """
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text) # Remove non-alphanumeric chars
    text = re.sub(r'[\s_-]+', '-', text)    # Replace spaces/underscores with single dash
    text = re.sub(r'^-+', '', text)         # Remove dashes from start
    text = re.sub(r'-+$', '', text)         # Remove dashes from end
    return text

def parse_html_content_preview(html_content, num_words=50):
    """
    Parses HTML content, extracts text for preview, and returns a truncated version.
    """
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

def main():
    try:
        blogger_api_key = get_secret("BLOGGER_API_KEY")
        blog_id = get_secret("BLOG_ID")

        print("Fetching Blogger posts...")
        posts_data = get_blogger_posts(blog_id, blogger_api_key, max_results=10)

        if posts_data:
            # Tentukan direktori output untuk halaman-halaman yang dihasilkan
            # Ini akan menjadi direktori 'gh-pages' atau 'docs'
            output_dir = os.path.join(os.path.dirname(__file__)) # Output di root yang sama dengan main.py
            
            # Pastikan direktori output ada
            os.makedirs(output_dir, exist_ok=True) # Buat jika belum ada

            # Inisialisasi Jinja2 Environment
            template_dir = os.path.join(os.path.dirname(__file__), 'templates')
            if not os.path.isdir(template_dir):
                raise FileNotFoundError(f"Template directory not found: {template_dir}")
            template_loader = FileSystemLoader(template_dir)
            env = Environment(loader=template_loader)
            
            # Muat template utama (index) dan template artikel tunggal
            index_template = env.get_template('index_template.html')
            single_post_template = env.get_template('single_post_template.html')

            processed_posts = []
            for post in posts_data.get('items', []):
                # Buat slug untuk nama file artikel penuh
                post_slug = slugify(post.get('title', 'untitled-post'))
                post_filename = f"{post_slug}.html"
                
                # Tambahkan URL relatif untuk tautan di index.html
                post['detail_url'] = post_filename

                # Proses konten untuk pratinjau di index.html
                raw_html_content = post.get('content')
                post['parsed_content'] = parse_html_content_preview(raw_html_content, num_words=50)
                
                processed_posts.append(post)

                # --- Generasi Halaman Detail Postingan ---
                # Render template artikel tunggal dengan data postingan penuh
                # Gunakan 'content' asli (yang mungkin HTML) untuk halaman detail
                single_post_html = single_post_template.render(post=post)
                
                # Simpan halaman detail postingan ke file terpisah
                single_post_file_path = os.path.join(output_dir, post_filename)
                with open(single_post_file_path, "w", encoding="utf-8") as f:
                    f.write(single_post_html)
                print(f"Generated: {single_post_file_path}")

            # --- Generasi Halaman Index ---
            # Render template index dengan data postingan yang sudah diproses
            index_html = index_template.render(posts=processed_posts)

            # Simpan halaman index.html
            index_file_path = os.path.join(output_dir, 'index.html')
            with open(index_file_path, "w", encoding="utf-8") as f:
                f.write(index_html)
            print(f"Generated: {index_file_path}")

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
