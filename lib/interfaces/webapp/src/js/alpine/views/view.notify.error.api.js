export default () => ({

    init() {
        this.$nextTick(() => {
            // Unlock magic button
            this.$store.app.appMagicButtonIsLocked = false;

            // Get current token
            const { apiToken: currentApiToken } = this.$store.api;

            // Get api status code
            const { statusCode } = this.$store.api.apiResponse;

            // Reset token if invalid/expired
            this.$store.api.apiToken = 
                statusCode === 401
                    ? ""
                    : currentApiToken;
        });
    },

    get notifyErrorApi() {
        return this.$store.api.apiResponse?.data?.detail;
    },

    magicButton: {

        ["label"]: "prev",

        ["action"]() {
            this.$store.api.apiToken 
                ? this.navigationGoTo("dropzone.data")
                : this.navigationGoTo("/");
        }
    }
});
