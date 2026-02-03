/**
 * Player: handles HLS playback with native retry behavior
 */
class Player {
    constructor(videoElement, streamUrl) {
        this.video = videoElement;
        this.streamUrl = streamUrl;
        this.hls = null;
        this.loadingText = document.getElementById('loading-text');
        this.errorCount = 0;
        this.maxErrors = 10;
    }

    start() {
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
            // Let Hls.js handle retries
            manifestLoadingMaxRetry: 20,
            manifestLoadingRetryDelay: 1000,
            fragLoadingMaxRetry: 10,
            fragLoadingRetryDelay: 1000,
            startLevel: 0
        });

        this.hls.loadSource(this.streamUrl);
        this.hls.attachMedia(this.video);

        // Update loading text on retry
        this.hls.on(Hls.Events.MANIFEST_LOADING, () => {
            if (this.loadingText) {
                this.loadingText.textContent = 'Loading manifest...';
            }
        });

        this.hls.on(Hls.Events.MANIFEST_PARSED, () => {
            this.hideLoading();
            this.video.play().catch(e => {
                console.log('Autoplay blocked, waiting for user');
            });
        });

        this.hls.on(Hls.Events.ERROR, (event, data) => {
            if (data.fatal) {
                this.handleFatalError(data);
            }
        });
    }

    initNative() {
        // Safari native HLS - browser handles all retries
        this.video.src = this.streamUrl;

        this.video.addEventListener('loadedmetadata', () => {
            this.hideLoading();
            this.video.play().catch(e => console.log('Autoplay blocked'));
        });

        this.video.addEventListener('waiting', () => {
            if (this.loadingText) {
                this.loadingText.textContent = 'Buffering...';
            }
        });

        this.video.addEventListener('playing', () => {
            this.hideLoading();
        });

        this.video.addEventListener('error', () => {
            const error = this.video.error;
            if (error && error.code === 2) {
                // Network error - browser is retrying
                this.errorCount++;
                if (this.loadingText) {
                    this.loadingText.textContent = `Retrying... (${this.errorCount})`;
                }
                if (this.errorCount > this.maxErrors) {
                    this.showError('Stream failed to load after multiple attempts');
                }
            } else {
                this.showError('Playback error');
            }
        });
    }

    handleFatalError(data) {
        if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
            // Hls.js already retrying, just update UI
            this.errorCount++;
            if (this.loadingText) {
                this.loadingText.textContent = `Retrying... (${this.errorCount})`;
            }
            if (this.errorCount > this.maxErrors) {
                this.showError('Stream failed to load after multiple attempts');
                this.hls.destroy();
            } else {
                this.hls.startLoad();
            }
        } else {
            this.showError('Playback error: ' + data.details);
        }
    }

    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) loading.style.display = 'none';
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