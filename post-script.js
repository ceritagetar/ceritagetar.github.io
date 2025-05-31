const API_KEY = 'AIzaSyDL33-qN4ylKeMIFcOQHw0mwn8Dv8HZH8k';
const BLOG_ID = '4310151456111498512';

const postDetailContainer = document.getElementById('post-detail-container');

async function fetchSingleBlogPost() {
    // Ambil ID postingan dari URL (misalnya: post.html?id=12345)
    const urlParams = new URLSearchParams(window.location.search);
    const postId = urlParams.get('id');

    if (!postId) {
        postDetailContainer.innerHTML = '<p class="error-message">ID artikel tidak ditemukan di URL.</p>';
        return; // Hentikan fungsi jika tidak ada ID
    }

    try {
        postDetailContainer.innerHTML = '<p class="loading-message">Memuat artikel lengkap...</p>';

        // Panggil Blogger API untuk mendapatkan satu postingan spesifik
        const response = await fetch(`https://www.googleapis.com/blogger/v3/blogs/${BLOG_ID}/posts/${postId}?key=${API_KEY}`);

        if (!response.ok) {
            throw new Error(`Error: ${response.status} - ${response.statusText}. Pastikan ID artikel benar atau blog publik.`);
        }

        const post = await response.json();

        if (post) {
            postDetailContainer.innerHTML = ''; // Hapus pesan loading

            // Judul Postingan Lengkap
            const postFullTitle = document.createElement('h2');
            postFullTitle.className = 'post-full-title';
            postFullTitle.textContent = post.title;
            postDetailContainer.appendChild(postFullTitle);

            // Tanggal Publikasi Lengkap
            const postFullDate = document.createElement('span');
            const dateOptions = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short' };
            postFullDate.textContent = `Dipublikasikan pada: ${new Date(post.published).toLocaleDateString('id-ID', dateOptions)}`;
            postFullDate.className = 'post-full-date';
            postDetailContainer.appendChild(postFullDate);

            // Konten Postingan Lengkap
            const postFullContent = document.createElement('div');
            postFullContent.className = 'post-full-content';
            postFullContent.innerHTML = post.content;
            postDetailContainer.appendChild(postFullContent);

            // Perbarui judul halaman di browser
            document.title = `${post.title} - Blog Saya`;

        } else {
            postDetailContainer.innerHTML = '<p class="error-message">Artikel tidak ditemukan.</p>';
        }

    } catch (error) {
        console.error('Terjadi kesalahan saat memuat artikel:', error);
        postDetailContainer.innerHTML = `<p class="error-message">Maaf, terjadi kesalahan saat memuat artikel: ${error.message}.</p>`;
    }
}

fetchSingleBlogPost();
