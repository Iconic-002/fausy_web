async function fetchStyles() {
    try {
        // This fetches the list from your backend
        const response = await fetch('http://127.0.0.1:5000/api/styles/');
        const styles = await response.json();
        const gallery = document.getElementById('styleGallery');
        
        gallery.innerHTML = styles.map(s => `
            <div class="style-card">
                ${s.video_url ? 
                    `<video src="${s.video_url}" autoplay muted loop playsinline></video>` : 
                    `<img src="${s.image_url}" alt="${s.name}">`
                }
                <h4>${s.name}</h4>
                <p style="font-size: 0.8rem; color: #666;">Ksh ${s.price}</p>
            </div>
        `).join('');
    } catch (err) {
        console.log("Error loading gallery styles.");
    }
}

// Make sure this runs when the page opens
window.addEventListener('DOMContentLoaded', fetchStyles);