# main.py
from utils import get_secret, get_blogger_posts

def main():
    try:
        # Get secret variables
        blogger_api_key = get_secret("BLOGGER_API_KEY")
        blog_id = get_secret("BLOG_ID")

        print("Fetching Blogger posts...")
        posts_data = get_blogger_posts(blog_id, blogger_api_key)

        if posts_data:
            print("\nSuccessfully fetched posts:")
            for post in posts_data.get('items', []):
                print(f"- Title: {post.get('title')}")
                print(f"  URL: {post.get('url')}\n")
        else:
            print("No posts found or an error occurred.")

    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
