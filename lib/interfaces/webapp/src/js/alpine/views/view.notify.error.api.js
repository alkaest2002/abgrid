export default () => ({

    init() {
        this.$nextTick(() => {
            // Unlock magic button
            this.$store.app.appMagicButtonIsLocked = false;

            // Save token refresh flag to store
            this.$store.api.apiTokenIsInvalid = 
                ["not_authenticated", "not_authorized", "invalid_or_expired_jwt_token"]
                    .includes(this.$store.api.apiResponse.data.detail);
            });
    },

    destroy() {
        // Reset api and app Responses
        this.$store.api.apiResponse = {};
        this.$store.data.dataYAMLError = {};
    },

    get notifyErrorApi() {
        return this.$store.api.apiResponse?.data?.detail;
    },

    magicButton: {

        ["label"]: "prev",

        ["action"]() {
            !this.$store.api.apiTokenIsInvalid && this.navigationGoTo("dropzone.data");
            this.$store.api.apiTokenIsInvalid && this.navigationGoTo("/");
        }
    }
});
