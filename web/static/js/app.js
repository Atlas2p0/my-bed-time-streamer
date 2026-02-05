let library = [];
let searchQuery = '';

async function loadData() {
    const res = await fetch('/api/library');
    library = await res.json();
    renderLibrary();
    initSearch();
}

function initSearch() {
    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        renderLibrary();
    });
}

function getFilteredLibrary() {
    if (!searchQuery) return library;
    
    return library.filter(folder => {
        if (folder.folder_name.toLowerCase().includes(searchQuery)) {
            return true;
        }
        return folder.episodes.some(ep => 
            ep.name.toLowerCase().includes(searchQuery)
        );
    });
}

function renderLibrary() {
    const grid = document.getElementById('library-grid');
    const resultsInfo = document.getElementById('search-results-info');
    const filtered = getFilteredLibrary();
    
    grid.innerHTML = '';
    
    if (searchQuery) {
        const totalMovies = filtered.reduce((sum, f) => sum + f.episodes.length, 0);
        resultsInfo.textContent = `Found ${filtered.length} folders, ${totalMovies} movies`;
    } else {
        resultsInfo.textContent = '';
    }
    
    if (filtered.length === 0) {
        grid.innerHTML = `<div class="no-results">No movies found matching "${searchQuery}"</div>`;
        return;
    }
    
    filtered.forEach((item) => {
        const originalIndex = library.indexOf(item);
        
        const card = document.createElement('div');
        card.className = 'folder-card';
        card.onclick = () => {
            // Navigate to movie page, clearing any search state
            window.location.href = `/movie?f=${originalIndex}`;
        };
        
        let episodeInfo = `${item.episodes.length} Episodes`;
        if (searchQuery) {
            const matching = item.episodes.filter(ep => 
                ep.name.toLowerCase().includes(searchQuery)
            ).length;
            if (matching > 0 && matching < item.episodes.length) {
                episodeInfo = `${matching} of ${item.episodes.length} match`;
            }
        }
        
        card.innerHTML = `
            <div style="font-size: 50px;">🎬</div>
            <h3>${highlightMatch(item.folder_name)}</h3>
            <p style="color: #888;">${episodeInfo}</p>
        `;
        grid.appendChild(card);
    });
}

function highlightMatch(text) {
    if (!searchQuery) return text;
    const regex = new RegExp(`(${escapeRegex(searchQuery)})`, 'gi');
    return text.replace(regex, '<mark style="background: #007bff; color: white; padding: 2px 4px; border-radius: 4px;">$1</mark>');
}

function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

loadData();