export default () => ({

    queueAbortController: null,
    queueTimerId: null,
    queueVisualTimerId: null,
    queueTimerDuration: 15 * 1000,
    queueVisualTimeRemaining: 0,
    queueAttemptsCount: 0,

    init() {
        // Init abort controller for cleanup
        this.queueAbortController = new AbortController();

        // Unlock magic button and start timers
        this.$nextTick(() => {
            this.$store.app.appMagicButtonIsLocked = false;
            this.startVisualTimer();
            this.queueReapeter();
        });
    },

    destroy() {
        // Abort any ongoing requests
        this.queueAbortController?.abort();
        // Clear both timers
        clearTimeout(this.queueTimerId);
        clearInterval(this.queueVisualTimerId);
        this.queueTimerId = null;
        this.queueVisualTimerId = null;
    },

    get queueTimerDurationInSeconds() {
        return this.queueTimerDuration / 1000;
    },

    startVisualTimer() {
        // Clear existing timer first to prevent leaks
        if (this.queueVisualTimerId) {
            clearInterval(this.queueVisualTimerId);
            this.queueVisualTimerId = null;
        }

        // Reset visual timer
        this.queueVisualTimeRemaining = this.queueTimerDurationInSeconds;

        // Start countdown with auto-stop
        this.queueVisualTimerId = setInterval(() => {
            this.queueVisualTimeRemaining--;
            if (this.queueVisualTimeRemaining <= 0) {
                clearInterval(this.queueVisualTimerId);
                this.queueVisualTimerId = null;
            }
        }, 1000);
    },

    queueReapeter() {
        this.queueTimerId = setTimeout(async () => {

            // Clear visual timer before making request
            if (this.queueVisualTimerId) {
                clearInterval(this.queueVisualTimerId);
                this.queueVisualTimerId = null;
            }

            try {
                const shouldContinue = await this.queueMakeApiRequest();

                if (shouldContinue) {
                    this.queueAttemptsCount++;
                    this.startVisualTimer();
                    this.queueReapeter();
                }
            } catch (error) {
                this.navigationGoTo("notify.error.api");
            }
        }, this.queueTimerDuration);
    },

    async queueMakeApiRequest() {
        try {
            const apiRequest = JSON.parse(JSON.stringify(this.$store.api.apiRequest));

            const { statusCode } = await this.apiProcessRequest(apiRequest, {
                signal: this.queueAbortController?.signal
            });

            // Only continue retrying on 429
            if (statusCode === 429) {
                return true;
            }

            // Handle success
            if (statusCode === 200) {
                const { endpoint } = this.$store.api.apiRequest;
                const navigationMap = {
                    "api/group": "dropzone.data",
                    "api/report": "notify.report",
                    "api/report/step_1": "multistep.sociogram",
                    "api/report/step_2": "multistep.json",
                    "api/report/step_3": "multistep.report"
                };
                if (navigationMap[endpoint]) {
                    this.navigationGoTo(navigationMap[endpoint]);
                }
            } else {
                // Any other error
                this.navigationGoTo("notify.error.api");
            }
        } catch (error) {
            if (error.name !== 'AbortError') {
                throw error;
            }
        }
    },

    magicButton: {
        ["label"]: "home",

        ["action"]() {
            this.navigationGoTo("/");
        }
    }
});
