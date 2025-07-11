export default () => ({

    initToast() {
        // Whatch for several changes that needs to be tosatified
        this.$watch("$store.abgrid.appIsOnline", (appIsOnline) => this.toastifyAppIsOnline(appIsOnline));
        this.$watch("$store.abgrid.appResponse", (appResponse) => this.toastifyAppResponse(appResponse));
        this.$watch("$store.abgrid.apiResponse", (apiResponse) => this.toastifyApiResponse(apiResponse));
    },

    toast: {
        statusCode: null,
        statusClass: "",
        statusMessage: "",
    },
    
    toastVisible: false,
    
    toastTimeout: null,
    
    toastDuration: 3000,

    toastShow(statusCode, statusMessage) {
        const statusClass = statusCode < 400
            ? "bg-green-200 text-green-700"
            : "bg-red-200 text-red-700";
        this.toast = Object.assign(this.toast, { statusCode, statusClass, statusMessage });
        this.toastVisible = true;
        this.toastTimeout = setTimeout(() => this.toastReset(), this.toastDuration);
    },

    toastReset() {
        clearTimeout(this.toastTimeout);
        this.toastVisible = false;
        this.toastQueue = {
            statusCode: null,
            statusClass: "",
            statusMessage: "",
        };
    },

    toastifyAppIsOnline(appIsOnline) {
        const statusCode = appIsOnline ? 200 : 400;
        const message = appIsOnline ? "app_is_online" : "app_is_offline";
        this.toastShow(statusCode, this.$t(message));
    },

    toastifyAppResponse(appResponse) {
        // Do nothing if app reponse is void
        if (Object.keys(appResponse).length === 0) return;
        const { statusCode = 200, message = "errros.unknown_issue_occurred" } = appResponse;
        this.toastShow(statusCode, this.$t(message));
    },

    toastifyApiResponse(apiResponse) {
        // Do nothing if api reponse is void
        if (!Object.keys(this.$store.abgrid.apiResponse).length)
            return;
        // Destructure api request
        const { endpoint = "" } = this.$store.abgrid.apiRequest;
        // Destructure api response
        const { statusCode = 500 } = apiResponse;
        // Manage different scenarios
        switch (endpoint) {
            case "api/token":
                return this.toastShow(200, this.$t("success.session_was_initialized"));
            case "api/report":
            case "api/group":
                return statusCode == 200
                    ? this.toastShow(statusCode, this.$t("success.report_was_generated"))
                    : this.toastShow(statusCode, this.$t("errors.report_generation_failure"));
            default:
                this.toastShow(statusCode, str(detail));
        }
    },

    toastContainer: {
        ["x-show"]: "toastVisible",

        [":class"]: "toast.statusClass",

        ["@click"]() {
            this.toastReset();
        }
    },

    toastMessage: {
        ["x-text"]: "toast.statusMessage"
    }
});
