# main.py
import os
from utils import get_secret, get_blogger_posts
from jinja2 import Environment, FileSystemLoader # Impor Jinja2
from bs4 import BeautifulSoup # Impor BeautifulSoup

def parse_html_content(html_content, num_words=50):
    """
    Parses HTML content, extracts text, and returns a truncated version.
    """
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Menghapus tag script dan style untuk keamanan dan kebersihan
    for script in soup(["script", "style"]):
        script.extract()
    
    # Mendapatkan teks dari HTML
    text = soup.get_text()
    
    # Memisahkan teks menjadi kata-kata dan memotongnya
    words = text.split()
    truncated_words = words[:num_words]
    
    # Menggabungkan kembali kata-kata yang sudah dipotong dan menambahkan elipsis jika perlu
    preview_text = " ".join(truncated_words)
    if len(words) > num_words:
        preview_text += "..."
        
    return preview_text

def main():
    try:
        # Get secret variables
        blogger_api_key = get_secret("BLOGGER_API_KEY")
        blog_id = get_secret("BLOG_ID")

        print("Fetching Blogger posts...")
        posts_data = get_blogger_posts(blog_id, blogger_api_key, max_results=10) # Ambil lebih banyak postingan

        if posts_data:
            # Proses setiap postingan untuk memparsing konten HTML
            processed_posts = []
            for post in posts_data.get('items', []):
                # Ambil konten mentah dari API. Perhatikan bahwa 'content' adalah objek di Blogger API.
                # Kita perlu mengambil string HTML-nya menggunakan .get('content')
                raw_html = post.get('content') 
                
                # Parsing dan bersihkan konten HTML
                # Menambahkan kunci baru 'parsed_content' ke setiap objek post
                post['parsed_content'] = parse_html_content(raw_html, num_words=50) # Sesuaikan jumlah kata pratinjau
                processed_posts.append(post)

            # Inisialisasi lingkungan Jinja2 untuk memuat template dari folder 'templates'
            # Path ke folder 'templates' harus absolut agar Jinja2 bisa menemukannya di lingkungan GitHub Actions
            template_dir = os.path.join(os.path.dirname(__file__), 'templates')
            
            # Cek apakah direktori template ada
            if not os.path.isdir(template_dir):
                raise FileNotFoundError(f"Template directory not found: {template_dir}")

            template_loader = FileSystemLoader(template_dir)
            env = Environment(loader=template_loader)
            template = env.get_template('index_template.html')

            # Render template dengan data postingan yang sudah diproses
            output_html = template.render(posts=processed_posts)

            # Tulis output HTML ke file index.html
            output_file_path = os.path.join(os.path.dirname(__file__), 'index.html')
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(output_html)

            print(f"Successfully generated {output_file_path}")
        else:
            print("No posts found or an error occurred. index.html not generated.")

    except FileNotFoundError as e:
        print(f"Error: {e}. Make sure 'templates' folder and 'index_template.html' exist in the correct location.")
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
