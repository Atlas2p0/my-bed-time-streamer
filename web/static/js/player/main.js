/**
 * Player entry point
 */
document.addEventListener('DOMContentLoaded', () => {
    const streamUrl = '/hls/index.m3u8';
    const video = document.getElementById('video');

    const player = new Player(video, streamUrl);
    player.start();
});