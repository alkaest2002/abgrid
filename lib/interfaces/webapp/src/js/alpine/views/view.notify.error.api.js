export default () => ({

    destroy() {
        // Save token refresh flag to store
        this.$store.api.apiTokenIsInvalid = 
            this.$store.api.apiResponse.data.detail == "invalid_or_expired_jwt_token";
        // Reset api and app Responses
        this.$store.api.apiResponse = {};
        this.$store.data.dataYAMLError = {};
    },

    get notifyApiErrors() {
        return this.$store.api.apiResponse?.data?.detail;
    },

    magicButton: {

        ["label"]: "prev",

        ["action"]() {
            this.navigationGoTo("dropzone");
        }
    }
});
