export default () => ({

    destroy() {
        // Save token refresh flag to store
        this.$store.api.apiTokenIsInvalid = 
            ["not_authenticated", "not_authorized", "invalid_or_expired_jwt_token"]
                .includes(this.$store.api.apiResponse.data.detail);
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
            this.navigationGoTo("dropzone.data");
        }
    }
});
