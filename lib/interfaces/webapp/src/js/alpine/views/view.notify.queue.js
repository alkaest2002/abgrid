export default () => ({

    async init() {
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
        this.timeoutId = setTimeout(async () => {
            if (this.currentTry > 0) {
                try {
                    await this.makeApirequest();
                } finally {
                    this.currentTry -= 1;
                    this.reapeter();
                }
            }
        }, 30);
    },

    async makeApirequest() {
        // Create api request
        const apiRequest = {
            endpoint: "api/report",
            method: "POST",
            queryParams: {
                "language": this.$store.app.appLanguage,
                with_sociogram: this.dropzoneDataWithSociogram
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
