/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
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

    queueTimerDuration: 15 * 1000,

    queueVisualTimeRemaining: 0,

    queueAttemptsCount: 0,

    get queueTimerDurationInSeconds() {
        return this.queueTimerDuration / 1000;
    },

    startVisualTimer() {
        // Set initial time remaining for new visual timer
        this.queueVisualTimeRemaining = this.queueTimerDurationInSeconds;
        // Create an interval to update new visual timer every second
        this.queueVisualTimerId = setInterval(() => this.queueVisualTimeRemaining--, 1000);
    },

    queueReapeter() {
        this.queueTimerId = setTimeout(async () => {
            // Clear previous visual timer if set
            this.queueVisualTimerId !== null && clearInterval(this.queueVisualTimerId);
            // Make api request
            await this.queueMakeApiRequest();
            // Increment attempt count
            this.queueAttemptsCount++;
            // Reset the visual timer for the next attempt
            this.startVisualTimer();
            // Call queueReapeter indefinitely
            this.queueReapeter();
        }, this.queueTimerDuration);
    },

    async queueMakeApiRequest() {
        // Get last api request (the one that generated the queue error)
        const apiRequest = JSON.parse(JSON.stringify(this.$store.api.apiRequest));
        // Make api request again
        const { statusCode } = await this.apiProcessRequest(apiRequest);
        // On success
        if (statusCode == 200) {
            // get request endpoint
            const { endpoint } = this.$store.api.apiRequest;
            // Go to different pages on the base of endopoint
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
            this.navigationGoTo("/");
        }
    }
});
