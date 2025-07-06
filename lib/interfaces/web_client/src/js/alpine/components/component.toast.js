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
        const message = appIsOnline ? "App is online." : "App is offline.";
        this.toastPush(statusCode, message);
    },

    toastifyAppResponse(appResponse) {
        if (Object.keys(appResponse).length === 0) return;
        const { statusCode = 200, message = "An unknown issue occurred." } = appResponse;
        this.toastPush(statusCode, message);
    },

    toastifyApiResponse(apiResponse) {
        if (this.$store.abgrid.apiRequest?.endpoint === "api/token") {
            return this.toastPush(200, "Session was correctly initialized.");
        }
        const { statusCode = 200, detail = "No details provided." } = apiResponse.data;
        this.toastPush(statusCode, detail);
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
