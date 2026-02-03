/**
 * StreamPoller: aggressively polls for stream availability before starting playback
 */
class StreamPoller {
    constructor(streamUrl, options = {}) {
        this.streamUrl = streamUrl;
        this.interval = options.interval || 500;
        this.timeout = options.timeout || 30000;
        this.maxRetries = options.maxRetries || 60;
        this.onReady = options.onReady || (() => {});
        this.onError = options.onError || (() => {});
        this.onProgress = options.onProgress || (() => {});

        this.attempts = 0;
        this.startTime = Date.now();
        this.timer = null;
        this.aborted = false;
    }

    async checkStream() {
        if (this.aborted) return false;

        this.attempts++;
        const elapsed = Date.now() - this.startTime;

        try {
            const response = await fetch(this.streamUrl + '?_cb=' + Date.now(), {
                method: 'GET',
                cache: 'no-store'
            });

            if (response.ok) {
                const text = await response.text();
                if (text.includes('#EXTM3U')) {
                    this.onReady();
                    return true;
                }
            }
        } catch (e) {
            // Expected while stream is starting
        }

        this.onProgress(this.attempts, elapsed);

        if (elapsed >= this.timeout || this.attempts >= this.maxRetries) {
            this.onError('Timeout waiting for stream');
            return false;
        }

        this.timer = setTimeout(() => this.checkStream(), this.interval);
        return false;
    }

    start() {
        this.startTime = Date.now();
        this.checkStream();
        return this;
    }

    stop() {
        this.aborted = true;
        if (this.timer) {
            clearTimeout(this.timer);
            this.timer = null;
        }
    }
}