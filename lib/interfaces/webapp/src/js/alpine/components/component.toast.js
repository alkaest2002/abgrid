export default () => ({

    initToast() {
        // Whatch for several changes that needs to be tosatified
        this.$watch("$store.app.appIsOnline", (appIsOnline) => this.toastifyAppIsOnline(appIsOnline));
        this.$watch("$store.app.appResponse", (appResponse) => this.toastifyAppResponse(appResponse));
        this.$watch("$store.api.apiResponse", (apiResponse) => this.toastifyApiResponse(apiResponse));
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
        const message = appIsOnline ? "toast.online" : "toast.offline";
        this.toastShow(statusCode, this.$t(message));
    },

    toastifyAppResponse(appResponse) {
        // Do nothing if app reponse is void
        if (Object.keys(appResponse).length === 0) return;
        const { statusCode = 200, message = "toast.error" } = appResponse;
        this.toastShow(statusCode, this.$t(message));
    },

    toastifyApiResponse(apiResponse) {
        // Do nothing if api reponse is void
        if (!Object.keys(this.$store.api.apiResponse).length)
            return;
        // Destructure api request
        const { endpoint = "" } = this.$store.api.apiRequest;
        // Destructure api response
        const { statusCode = 500, data: { detail } } = apiResponse;
        // Manage different scenarios
        if (["api/report", "api/group"].includes(endpoint)) {
            return statusCode == 200
                ? this.toastShow(statusCode, this.$t("toast.success"))
                : this.toastShow(statusCode, this.$t("toast.error"));
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
        ["x-html"]: "toast.statusMessage"
    }
});
