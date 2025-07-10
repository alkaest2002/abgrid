export default () => ({

    initToast() {
        console.log("initToast");
        this.$watch("$store.abgrid.appIsOnline", (appIsOnline) => this.toastifyAppIsOnline(appIsOnline));
        this.$watch("$store.abgrid.appResponse", (appResponse) => this.toastifyAppResponse(appResponse));
        this.$watch("$store.abgrid.apiResponse", (apiResponse) => this.toastifyApiResponse(apiResponse));
    },

    toastQueue: [],
    toastVisible: false,
    toastTimeout: null,
    toastDuration: 3000,

    toastPush(statusCode, message) {
        const badgeClass = this.getBadgeClass(statusCode);
        this.toastQueue.push({ statusCode, message, badgeClass });
        if (!this.toastVisible) this.toastShowNext();
    },

    getBadgeClass(statusCode) {
        if (statusCode >= 200 && statusCode < 400) {
            return 'bg-green-700';
        } else if (statusCode >= 400 && statusCode < 600) {
            return 'bg-red-700';
        }
        return 'bg-gray-700';
    },

    toastShowNext() {
        clearTimeout(this.toastTimeout);
        this.toastVisible = true;
        this.toastTimeout = setTimeout(() => this.toastRemoveCurrent(), this.toastDuration);
    },

    toastRemoveCurrent() {
        this.toastVisible = false;
        this.toastQueue.shift();
        this.$nextTick(() => {
            if (this.toastQueue.length > 0) {
                this.toastShowNext();
            }
        });
    },

    toastifyAppIsOnline(appIsOnline) {
        const statusCode = appIsOnline ? 200 : 400;
        const message = appIsOnline ? "app_is_online" : "app_is_offline";
        this.toastPush(statusCode, this.$t(message));
    },

    toastifyAppResponse(appResponse) {
        if (Object.keys(appResponse).length === 0) return;
        const { statusCode = 200, message = "unknown_issue_occurred" } = appResponse;
        this.toastPush(statusCode, this.$t(message));
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
                return this.toastPush(200, this.$t("success.session_was_initialized"));
            case "api/report":
            case "api/group":
                return statusCode == 200
                    ? this.toastPush(200, this.$t("success.report_was_generated"))
                    : this.toastPush(statusCode, this.$t("errors.report_generation_failure"));
            default:
                this.toastPush(statusCode, str(detail));
        }
    },

    toastContainer: {
        ["x-show"]() {
            return this.toastVisible;
        },

        ["@click"]() {
            this.toastRemoveCurrent();
        },
    },

    toastBadge: {
        [":class"]() {
            return this.toastQueue[0]?.badgeClass;
        },

        ["x-text"]() {
            return this.toastQueue.length;
        }
    },

    toastMessage: {
        ["x-text"]() {
            return this.toastQueue[0]?.message;
        }
    }
});
