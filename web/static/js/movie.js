const urlParams = new URLSearchParams(window.location.search);
const folderIndex = parseInt(urlParams.get('f'));

let folder = null;
let availablePresets = [];

// Global functions for onclick
window.goBack = function() {
    window.location.href = '/';
};

window.stopStream = async function() {
    const statusBar = document.getElementById('status-bar');
    statusBar.textContent = 'Stopping stream...';
    statusBar.style.display = 'block';
    
    try {
        await fetch('/api/stop', { method: 'POST' });
        statusBar.textContent = 'Stream stopped';
        setTimeout(() => {
            statusBar.style.display = 'none';
        }, 2000);
    } catch (err) {
        statusBar.textContent = 'Error stopping stream';
        console.error('Stop error:', err);
    }
};

window.startEpisode = async function(epIdx) {
    const ep = folder.episodes[epIdx];
    const subPath = document.getElementById(`sub-${epIdx}`).value;
    const preset = document.getElementById(`preset-${epIdx}`).value;
    
    const statusBar = document.getElementById('status-bar');
    statusBar.textContent = `Preparing: ${ep.name}...`;
    statusBar.style.display = 'block';
    
    window.open('/player', 'bedtime-player');
    
    const probeRes = await fetch('/api/probe', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ path: ep.path })
    });
    const metadata = await probeRes.json();
    
    await fetch('/api/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            path: ep.path,
            preset: preset,
            sub_path: subPath,
            has_internal_subs: metadata.has_internal_subs,
            text_sub_index: metadata.text_sub_index,
            pgs_sub_index: metadata.pgs_sub_index
        })
    });
    
    statusBar.textContent = `NOW STREAMING: ${ep.name}`;
};

async function loadData() {
    const [libRes, preRes] = await Promise.all([
        fetch('/api/library'),
        fetch('/api/presets')
    ]);
    
    const library = await libRes.json();
    availablePresets = await preRes.json();
    
    folder = library[folderIndex];
    
    if (!folder) {
        document.getElementById('movie-title').textContent = 'Movie not found';
        return;
    }
    
    renderMovie();
}

function renderMovie() {
    document.getElementById('movie-title').textContent = folder.folder_name;
    document.getElementById('movie-info').textContent = 
        `${folder.episodes.length} episode${folder.episodes.length !== 1 ? 's' : ''}`;
    
    const list = document.getElementById('episodes-list');
    list.innerHTML = '';
    
    folder.episodes.forEach((ep, idx) => {
        const item = document.createElement('div');
        item.className = 'episode-item';
        
        let subOptions = `<option value="">None / Use Internal</option>`;
        folder.local_subs.forEach(s => {
            subOptions += `<option value="${s.path}">${s.name}</option>`;
        });
        
        let presetOptions = '';
        availablePresets.forEach(p => {
            const prettyName = p.replace(/_/g, ' ').toUpperCase();
            const selected = p === 'cpu_fast' ? 'selected' : '';
            presetOptions += `<option value="${p}" ${selected}>${prettyName}</option>`;
        });
        
        item.innerHTML = `
            <div class="episode-name">${ep.name}</div>
            <div class="options-row">
                <div class="option-group">
                    <label>Subtitles</label>
                    <select id="sub-${idx}">${subOptions}</select>
                </div>
                <div class="option-group">
                    <label>Quality</label>
                    <select id="preset-${idx}">${presetOptions}</select>
                </div>
                <div class="button-group">
                <button class="play" onclick="startEpisode(${idx})">▶ Play</button>
                    <button class="stop" onclick="stopStream()">⏹ Stop</button>
                </div>
            </div>
        `;
        
        list.appendChild(item);
    });
}

loadData();