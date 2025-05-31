// GANTI DENGAN API KEY DAN ID BLOG ANDA
const API_KEY = 'AIzaSyDL33-qN4ylKeMIFcOQHw0mwn8Dv8HZH8k';
const BLOG_ID = '4310151456111498512';

const postsContainer = document.getElementById('posts-container');

async function fetchBlogPosts() {
    try {
        // Hapus pesan loading awal
        postsContainer.innerHTML = '';

        // Panggil Blogger API
        const response = await fetch(`https://www.googleapis.com/blogger/v3/blogs/${BLOG_ID}/posts?key=${API_KEY}`);

        if (!response.ok) {
            // Tangani jika respons bukan 200 OK
            throw new Error(`Error: ${response.status} - ${response.statusText}. Pastikan API Key dan Blog ID benar serta blog publik.`);
        }

        const data = await response.json();

        // Pastikan ada postingan yang ditemukan
        if (data.items && data.items.length > 0) {
            data.items.forEach(post => {
                const postElement = document.createElement('div');
                postElement.className = 'post';

                // Judul Postingan
                const postTitle = document.createElement('h2');
                postTitle.textContent = post.title;
                postElement.appendChild(postTitle);

                // Tanggal Publikasi
                const postDate = document.createElement('span');
                const dateOptions = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
                postDate.textContent = `Dipublikasikan pada: ${new Date(post.published).toLocaleDateString('id-ID', dateOptions)}`;
                postDate.className = 'post-date';
                postElement.appendChild(postDate);

                // Konten Postingan (HTML dari Blogger)
                const postContent = document.createElement('div');
                postContent.className = 'post-content';
                // Gunakan innerHTML untuk menampilkan konten HTML dari Blogger
                postContent.innerHTML = post.content;
                postElement.appendChild(postContent);

                // Link "Baca Selengkapnya" ke postingan asli di Blogger
                const readMoreLink = document.createElement('a');
                readMoreLink.href = post.url;
                readMoreLink.target = '_blank'; // Buka di tab baru
                readMoreLink.className = 'read-more-link';
                readMoreLink.textContent = 'Baca Selengkapnya';
                postElement.appendChild(readMoreLink);

                postsContainer.appendChild(postElement);
            });
        } else {
            postsContainer.innerHTML = '<p class="loading-message">Tidak ada artikel yang ditemukan di blog ini.</p>';
        }

    } catch (error) {
        console.error('Terjadi kesalahan saat memuat artikel:', error);
        postsContainer.innerHTML = `<p class="error-message">Maaf, terjadi kesalahan saat memuat artikel: ${error.message}.</p>`;
    }
}

// Panggil fungsi saat halaman dimuat
fetchBlogPosts();
