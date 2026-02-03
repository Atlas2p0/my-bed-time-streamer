/**
 * Player: handles HLS playback once stream is ready
 */
class Player {
    constructor(videoElement, streamUrl) {
        this.video = videoElement;
        this.streamUrl = streamUrl;
        this.hls = null;
    }

    start() {
        const loadingText = document.getElementById('loading-text');
        if (loadingText) {
            loadingText.textContent = 'Buffering...';
        }

        if (Hls.isSupported()) {
            this.initHls();
        } else if (this.video.canPlayType('application/vnd.apple.mpegurl')) {
            this.initNative();
        } else {
            this.showError('HLS not supported in this browser');
        }
    }

    initHls() {
        this.hls = new Hls({
            enableWorker: true,
            lowLatencyMode: true,
            maxBufferLength: 30,
            maxBufferHole: 0.5,
            manifestLoadingTimeOut: 10000,
            manifestLoadingMaxRetry: 5,
            manifestLoadingRetryDelay: 500,
            fragLoadingTimeOut: 10000,
            fragLoadingMaxRetry: 5,
            fragLoadingRetryDelay: 500,
            startLevel: 0,
            autoStartLoad: true
        });

        this.hls.loadSource(this.streamUrl);
        this.hls.attachMedia(this.video);

        this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
            const loading = document.getElementById('loading');
            if (loading) loading.style.display = 'none';

            this.video.play().catch(e => {
                console.log('Autoplay blocked, waiting for user');
            });
        });

        this.hls.on(Hls.Events.ERROR, (event, data) => {
            console.error('HLS error:', data);
            if (data.fatal) {
                this.handleFatalError(data);
            }
        });
    }

    initNative() {
        this.video.src = this.streamUrl;

        this.video.addEventListener('loadedmetadata', () => {
            const loading = document.getElementById('loading');
            if (loading) loading.style.display = 'none';

            this.video.play();
        });

        this.video.addEventListener('error', () => {
            this.showError('Failed to load stream');
        });
    }

    handleFatalError(data) {
        if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
            this.hls.startLoad();
        } else {
            this.showError('Playback error: ' + data.details);
        }
    }

    showError(msg) {
        const loading = document.getElementById('loading');
        const errorDiv = document.getElementById('error');
        const errorText = document.getElementById('error-text');

        if (loading) loading.style.display = 'none';
        if (errorText) errorText.textContent = msg;
        if (errorDiv) errorDiv.style.display = 'block';
    }

    destroy() {
        if (this.hls) {
            this.hls.destroy();
            this.hls = null;
        }
    }
}