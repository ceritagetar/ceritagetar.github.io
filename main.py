# main.py (Revisi untuk output ke folder 'dist')
import os
import re
from utils import get_secret, get_blogger_posts
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup

def slugify(text):
    """
    Converts text to a URL-friendly slug.
    """
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+', '', text)
    text = re.sub(r'-+$', '', text)
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
            # Tentukan direktori output sebagai subfolder 'dist' di direktori kerja saat ini
            # os.getcwd() akan mengembalikan direktori tempat workflow dijalankan
            output_dir = os.path.join(os.getcwd(), 'dist') # <-- Ini poin utamanya!
            
            # Pastikan folder 'dist' dibuat jika belum ada
            os.makedirs(output_dir, exist_ok=True) 
            print(f"Output directory created/ensured: {output_dir}")

            # Path ke folder 'templates' relatif terhadap 'main.py'
            template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
            
            if not os.path.isdir(template_dir):
                raise FileNotFoundError(f"Template directory not found: {template_dir}")
            
            template_loader = FileSystemLoader(template_dir)
            env = Environment(loader=template_loader)
            
            index_template = env.get_template('index_template.html')
            single_post_template = env.get_template('single_post_template.html')

            processed_posts = []
            for post in posts_data.get('items', []):
                post_slug = slugify(post.get('title', 'untitled-post'))
                post_filename = f"{post_slug}.html"
                
                # Tautan di index.html harus tetap relatif ke root situs (/)
                # agar saat diakses dari ceritagetat.github.io/index.html bisa ke ceritagetat.github.io/post-name.html
                post['detail_url'] = f"/{post_filename}" 

                raw_html_content = post.get('content')
                post['parsed_content'] = parse_html_content_preview(raw_html_content, num_words=50)
                
                processed_posts.append(post)

                # --- Generasi Halaman Detail Postingan ---
                single_post_html = single_post_template.render(post=post)
                
                single_post_file_path = os.path.join(output_dir, post_filename) # Menyimpan ke dalam 'dist'
                with open(single_post_file_path, "w", encoding="utf-8") as f:
                    f.write(single_post_html)
                print(f"Generated: {single_post_file_path}")

            # --- Generasi Halaman Index ---
            index_html = index_template.render(posts=processed_posts)

            index_file_path = os.path.join(output_dir, 'index.html') # Menyimpan ke dalam 'dist'
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
