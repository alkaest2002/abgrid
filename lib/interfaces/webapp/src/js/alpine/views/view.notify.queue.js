export default () => ({

    async init() {
        // Unlock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = false);
        // Try to make api request
        this.queueReapeter();
    },

    destroy() {
        // Clear timeout id
        clearTimeout(this.queueTimerId);
    },

    queueTimerTry: 10,

    queueTimerId: null,

    queueTimerDuration: 1000,

    get queueTimerDurationInSeconds() {
        return this.queueTimerDuration / 1000;
    },

    queueReapeter() {
        this.queueTimerId = setTimeout(async () => {
            if (this.queueTimerTry > 0) {
                await this.queueMakeApiRequest();
                console.log(this.queueTimerTry)
                this.queueTimerTry -= 1;
                this.queueReapeter();
            }
        }, this.queueTimerDuration);
    },

    async queueMakeApiRequest() {
        // Create api request
        const apiRequest = {
            endpoint: "fake/error",
            method: "GET",
            queryParams: {
                error_type: "too_many_concurrent_requests"
            },
            bodyData: JSON.parse(JSON.stringify(this.$store.data.dataJSON))
        };
        
        // Make api request to server
        const { statusCode } = await this.apiHandleRequest(apiRequest);

        console.log(statusCode)
        
        // On api success
        if (statusCode == 200) {
            // Go to report notification page
            this.navigationGoTo("notify.report");
        }
        // On api error except queue error
        else if (statusCode != 429) {
            // Go to error notification page 
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
