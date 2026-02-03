let library = [];
let availablePresets = [];

async function loadData() {
    const [libRes, preRes] = await Promise.all([
        fetch('/api/library'),
        fetch('/api/presets')
    ])
    library = await libRes.json();
    availablePresets = await preRes.json();
    renderLibrary();
}

function renderLibrary() {
    const grid = document.getElementById('library-grid');
    grid.innerHTML = '';
    library.forEach((item, index) => {
        const card = document.createElement('div');
        card.className = 'folder-card';
        card.onclick = () => showEpisodes(index);
        card.innerHTML = `
            <div style="font-size: 50px;">🎬</div>
            <h3>${item.folder_name}</h3>
            <p style="color: #888;">${item.episodes.length} Episodes</p>
        `;
        grid.appendChild(card);
    });
}

function showEpisodes(index) {
    const folder = library[index];
    document.getElementById('view-library').classList.add('hidden');
    document.getElementById('view-episodes').classList.remove('hidden');
    document.getElementById('current-folder-name').innerText = folder.folder_name;

    const list = document.getElementById('episode-list');
    list.innerHTML = '';

    folder.episodes.forEach((ep, epIdx) => {
        const row = document.createElement('div');
        row.className = 'episode-row';
        
        let subOptions = `<option value="">None / Use Internal</option>`;
        folder.local_subs.forEach(s => {
            subOptions += `<option value="${s.path}">${s.name}</option>`;
        });

        let presetOptions = '';
        availablePresets.forEach(p => {
            const prettyName = p.replace(/_/g, ' ').toUpperCase();
            presetOptions += `<option value="${p}">${prettyName}</option>`;
        });

        row.innerHTML = `
            <div style="flex: 1;"><strong>${ep.name}</strong></div>
            <div class="controls">
                <label>Subs:</label>
                <select id="sub-${index}-${epIdx}">${subOptions}</select>
                
                <label>Preset:</label>
                <select id="preset-${index}-${epIdx}">
                    ${presetOptions}
                </select>
                
                <button onclick="startEpisode(${index}, ${epIdx})">▶ Start Stream</button>
                <button class="stop" onclick="stopStream()">⏹ Stop</button>
            </div>
        `;
        list.appendChild(row);
    });
}

function showLibrary() {
    document.getElementById('view-library').classList.remove('hidden');
    document.getElementById('view-episodes').classList.add('hidden');
}

async function startEpisode(folderIdx, epIdx) {
    const folder = library[folderIdx];
    const ep = folder.episodes[epIdx];
    const subPath = document.getElementById(`sub-${folderIdx}-${epIdx}`).value;
    const preset = document.getElementById(`preset-${folderIdx}-${epIdx}`).value;

    const statusBar = document.getElementById('status-bar');
    statusBar.innerText = `Preparing: ${ep.name}...`;
    statusBar.classList.remove('hidden');

    // Open player in new tab immediately
    const playerWindow = window.open('/player', 'bedtime-player');

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

    statusBar.innerText = `NOW STREAMING: ${ep.name}`;
}

async function stopStream() {
    await fetch('/api/stop', { method: 'POST' });
    document.getElementById('status-bar').classList.add('hidden');
}

loadData();