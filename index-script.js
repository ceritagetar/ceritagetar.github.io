const API_KEY = 'AIzaSyDL33-qN4ylKeMIFcOQHw0mwn8Dv8HZH8k';
const BLOG_ID = '4310151456111498512';

const postsListContainer = document.getElementById('posts-list-container');

async function fetchBlogPostsSummary() {
    try {
        postsListContainer.innerHTML = ''; // Hapus pesan loading

        // Panggil Blogger API
        const response = await fetch(`https://www.googleapis.com/blogger/v3/blogs/${BLOG_ID}/posts?key=${API_KEY}`);

        if (!response.ok) {
            throw new Error(`Error: ${response.status} - ${response.statusText}. Pastikan API Key dan Blog ID benar.`);
        }

        const data = await response.json();

        if (data.items && data.items.length > 0) {
            data.items.forEach(post => {
                const postSummaryElement = document.createElement('div');
                postSummaryElement.className = 'post-summary';

                // Judul Postingan (yang bisa diklik)
                const postTitle = document.createElement('h2');
                const titleLink = document.createElement('a');
                titleLink.href = `post.html?id=${post.id}`; // Link ke halaman detail dengan ID artikel
                titleLink.textContent = post.title;
                postTitle.appendChild(titleLink);
                postSummaryElement.appendChild(postTitle);

                // Tanggal Publikasi
                const postDate = document.createElement('span');
                const dateOptions = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short' };
                postDate.textContent = `Dipublikasikan pada: ${new Date(post.published).toLocaleDateString('id-ID', dateOptions)}`;
                postDate.className = 'post-date';
                postSummaryElement.appendChild(postDate);

                // Snippet Konten (ambil sebagian dari konten penuh)
                const snippetElement = document.createElement('div');
                snippetElement.className = 'snippet';
                // Hapus tag HTML dari konten untuk snippet bersih
                const plainTextContent = post.content.replace(/<[^>]*>?/gm, '');
                snippetElement.textContent = plainTextContent.substring(0, 200) + '...'; // Ambil 200 karakter pertama
                postSummaryElement.appendChild(snippetElement);

                // Link "Baca Selengkapnya" (tombol terpisah)
                const readFullLink = document.createElement('a');
                readFullLink.href = `post.html?id=${post.id}`;
                readFullLink.className = 'read-full-link';
                readFullLink.textContent = 'Baca Selengkapnya →';
                postSummaryElement.appendChild(readFullLink);

                postsListContainer.appendChild(postSummaryElement);
            });
        } else {
            postsListContainer.innerHTML = '<p class="loading-message">Tidak ada artikel yang ditemukan.</p>';
        }

    } catch (error) {
        console.error('Terjadi kesalahan saat memuat daftar artikel:', error);
        postsListContainer.innerHTML = `<p class="error-message">Maaf, terjadi kesalahan saat memuat daftar artikel: ${error.message}.</p>`;
    }
}

fetchBlogPostsSummary();
