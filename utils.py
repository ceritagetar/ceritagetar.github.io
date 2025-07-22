# utils.py
import os
import requests

def get_secret(key):
    """
    Retrieves a secret variable from the environment.
    """
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Environment variable '{key}' not set.")
    return value

def get_blogger_posts(blog_id, api_key, max_results=5):
    """
    Fetches a list of posts from a specified Blogger blog.
    """
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts?key={api_key}&maxResults={max_results}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Blogger posts: {e}")
        return None
