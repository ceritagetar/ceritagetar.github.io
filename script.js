const API_KEY = 'AIzaSyDL33-qN4ylKeMIFcOQHw0mwn8Dv8HZH8k'; // API Key Anda
const BLOG_ID = '4310151456111498512'; // ID Blog Anda

const postsContainer = document.getElementById('posts-container');

async function fetchBlogPosts() {
    try {
        // Hapus pesan loading awal
        postsContainer.innerHTML = '';

        // Panggil Blogger API untuk mendapatkan daftar postingan
        const response = await fetch(`https://www.googleapis.com/blogger/v3/blogs/${BLOG_ID}/posts?key=${API_KEY}`);

        if (!response.ok) {
            // Tangani jika respons bukan 200 OK
            throw new Error(`Error: ${response.status} - ${response.statusText}. Pastikan API Key dan Blog ID benar, serta blog Anda bersifat publik.`);
        }

        const data = await response.json();

        // Periksa apakah ada postingan yang ditemukan
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
                // Atur format tanggal sesuai keinginan Anda
                const dateOptions = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short' };
                postDate.textContent = `Dipublikasikan pada: ${new Date(post.published).toLocaleDateString('id-ID', dateOptions)}`;
                postDate.className = 'post-date';
                postElement.appendChild(postDate);

                // Konten Postingan (HTML dari Blogger)
                const postContent = document.createElement('div');
                postContent.className = 'post-content';
                // Gunakan innerHTML untuk menampilkan konten HTML dari Blogger secara langsung
                postContent.innerHTML = post.content;
                postElement.appendChild(postContent);

                postsContainer.appendChild(postElement);
            });
        } else {
            postsContainer.innerHTML = '<p class="loading-message">Tidak ada artikel yang ditemukan di blog ini.</p>';
        }

    } catch (error) {
        // Tangani kesalahan dan tampilkan pesan ke pengguna
        console.error('Terjadi kesalahan saat memuat artikel:', error);
        postsContainer.innerHTML = `<p class="error-message">Maaf, terjadi kesalahan saat memuat artikel: ${error.message}. Silakan cek konsol browser untuk detail lebih lanjut.</p>`;
    }
}

// Panggil fungsi untuk mengambil dan menampilkan postingan saat halaman dimuat
fetchBlogPosts();
