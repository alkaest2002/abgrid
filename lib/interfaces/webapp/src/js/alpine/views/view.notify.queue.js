export default () => ({

    async init() {
        // Unlock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = false);
        // Initialize visual timer
        this.startVisualTimer();
        // Initialize timer to call api continuosly
        this.queueReapeter();
    },

    destroy() {
        // Clear timers
        clearTimeout(this.queueTimerId);
        clearInterval(this.queueVisualTimerId);
    },

    queueTimerId: null,

    queueVisualTimerId: null,

    queueTimerDuration: 30 * 1000,

    queueVisualTimeRemaining: 0,

    queueAttemptsCount: 0,

    get queueTimerDurationInSeconds() {
        return this.queueTimerDuration / 1000;
    },

    startVisualTimer() {
        // Clear previous visual timer if set
        this.queueVisualTimerId !== null && clearInterval(this.queueVisualTimerId);
        // Set initial time remaining for new visual timer
        this.queueVisualTimeRemaining = this.queueTimerDurationInSeconds;
        // Create an interval to update new visual timer every second
        this.queueVisualTimerId = setInterval(() => this.queueVisualTimeRemaining--, 1000);
    },

    queueReapeter() {
        this.queueTimerId = setTimeout(async () => {
            // make api request
            await this.queueMakeApiRequest();
            // Increment attempt count
            this.queueAttemptsCount++;
            // Reset the visual timer for the next attempt
            this.startVisualTimer();
            // Continuously call queueReapeter indefinitely
            this.queueReapeter();
        }, this.queueTimerDuration);
    },

    async queueMakeApiRequest() {
        
        // Get last request
        const apiRequest = JSON.parse(JSON.stringify(this.$store.api.apiRequest));
        // Make api request
        const { statusCode } = await this.apiHandleRequest(apiRequest);

        if (statusCode == 200) {
            // get request endpoint
            const { endpoint } = this.$store.api.apiRequest;
            
            // Go to different pages relative to endopoint
            endpoint == "api/token" && this.navigationGoTo("group");
            endpoint == "api/group" && this.navigationGoTo("dropzone.data");
            endpoint == "api/report" && this.navigationGoTo("notify.report");
        // On error other than too many requests
        } else if (statusCode != 429) {
            // Go to api error page
            this.navigationGoTo("notify.error.api");
        }
    },

    magicButton: {
        ["label"]: "home",

        ["action"]() {
            this.navigationGoTo("home");
        }
    }
});
