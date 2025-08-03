export default () => ({

    init() {
        this.$nextTick(() => {
            // Unlock magic button
            this.$store.app.appMagicButtonIsLocked = false;

            // Unauthorized errors
            const unauthorized = ["not_authenticated", "not_authorized", "invalid_or_expired_jwt_token"];

            // Get current token
            const { apiToken: currentApiToken } = this.$store.api;

            // If error is included in unauthorized list
            this.$store.api.apiToken = 
                unauthorized
                    .includes(this.$store.api.apiResponse.data.detail) 
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
