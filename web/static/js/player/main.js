/**
 * Player entry point - initializes StreamPoller and Player
 */
document.addEventListener('DOMContentLoaded', () => {
    const streamUrl = '/hls/index.m3u8';
    const video = document.getElementById('video');
    const loadingText = document.getElementById('loading-text');

    const poller = new StreamPoller(streamUrl, {
        interval: 500,
        timeout: 30000,
        onReady: () => {
            const player = new Player(video, streamUrl);
            player.start();
        },
        onError: (msg) => {
            const errorText = document.getElementById('error-text');
            const errorDiv = document.getElementById('error');
            if (errorText) errorText.textContent = msg;
            if (errorDiv) errorDiv.style.display = 'block';
        },
        onProgress: (attempts, elapsed) => {
            if (loadingText) {
                loadingText.textContent = `Waiting for stream... (${attempts})`;
            }
        }
    });

    poller.start();
});