export default () => ({

    async init() {
        console.log("queue")
        // Unlock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = false);
        // Try to make api request
        this.reapeter();
    },

    destroy() {
        // Clear timeout id
        clearTimeout(this.timeoutId);
    },

    currentTry: 10,

    timeoutId: null,

    reapeter() {
        console.log("repeater")
        this.timeoutId = setTimeout(async () => {
            if (this.currentTry > 0) {
                console.log("request")
                await this.makeApirequest();
                this.currentTry -= 1;
                this.reapeter();
            }
        }, 5000);
    },

    async makeApirequest() {
        console.log("makeApirequest")
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
