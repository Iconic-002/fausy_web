async function fetchStyles() {
    try {
        // CHANGED: Point to your live Render backend instead of localhost
        const response = await fetch('https://fausy-web.onrender.com/api/styles/');
        
        if (!response.ok) throw new Error("Failed to fetch styles");
        
        const styles = await response.json();
        const gallery = document.getElementById('styleGallery');
        
        if (!gallery) return; // Safety check

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
        console.error("Error loading gallery styles:", err);
        // Optional: show a small message to the user if it fails
        document.getElementById('styleGallery').innerHTML = "<p>Unable to load styles right now.</p>";
    }
}

// Ensure this runs when the page opens
window.addEventListener('DOMContentLoaded', fetchStyles);