export default () => ({

    async init() {
        // Unlock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = false);
        // Initialize the time remaining and start visual timer
        this.startVisualTimer();
        // Try to make api request
        this.queueReapeter();
    },

    destroy() {
        // Clear timeout and interval ids
        clearTimeout(this.queueTimerId);
        clearInterval(this.queueVisualTimerId);
    },

    queueTimerId: null,

    queueVisualTimerId: null,

    queueTimerTry: 10,

    queueTimerDuration: 30 * 1000,

    queueVisualTimeRemaining: 0,

    get queueTimerDurationInSeconds() {
        return this.queueTimerDuration / 1000;
    },

    startVisualTimer() {
        
        // Clear the previous interval if it exists
        if (this.queueVisualTimerId !== null) {
            clearInterval(this.queueVisualTimerId);
        }

        // Set initial time remaining
        this.queueVisualTimeRemaining = this.queueTimerDurationInSeconds;

        // Create an interval to update remaining time every second
        this.queueVisualTimerId = setInterval(() => {
            this.queueVisualTimeRemaining -= 1;
        }, 1000);
    },


    queueReapeter() {
        this.queueTimerId = setTimeout(async () => {
            if (this.queueTimerTry > 0) {
                await this.queueMakeApiRequest();
                this.queueTimerTry -= 1;
                // Reset the visual timer for the next attempt
                this.startVisualTimer();
                this.queueReapeter();
            }
        }, this.queueTimerDuration);
    },

    async queueMakeApiRequest() {
        const apiRequest = {
            endpoint: "fake/error",
            method: "GET",
            queryParams: {
                error_type: "too_many_concurrent_requests"
            },
            bodyData: JSON.parse(JSON.stringify(this.$store.data.dataJSON))
        };

        const { statusCode } = await this.apiHandleRequest(apiRequest);

        if (statusCode == 200) {
            this.navigationGoTo("notify.report");
        } else if (statusCode != 429) {
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
