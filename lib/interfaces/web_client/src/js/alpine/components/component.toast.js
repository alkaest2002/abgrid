export default () => ({

    toastQueue: [],
    toastVisible: false,
    toastTimeout: null,
    toastDuration: 3000,

    initToast() {
        // Log
        console.log("initToast")
        // Watch store props
        this.$watch("$store.abgrid.appIsOnline", (appIsOnline) => this.toastifyAppIsOnline(appIsOnline));
        this.$watch("$store.abgrid.appResponse", (appResponse) => this.toastifyAppResponse(appResponse));
        this.$watch("$store.abgrid.apiResponse", (apiResponse) => this.toastifyApiResponse(apiResponse));
    },

    toastPush(message) {
        this.toastQueue.push(message);
        if (!this.toastVisible) this.toastShowNext();
    },

    toastShowNext() {
        if (this.toastQueue.length === 0) return;
        clearTimeout(this.toastTimeout);
        this.toastVisible = true;
        this.toastTimeout = setTimeout(() => this.toastRemoveCurrent(), this.toastDuration);
    },

    toastRemoveCurrent() {
        this.toastQueue.shift();
        this.toastVisible = false;
        clearTimeout(this.toastTimeout);
        this.$nextTick(() => {
            if (this.toastQueue.length > 0) {
                this.toastShowNext();
            }
        })
    },

    toastifyAppIsOnline(appIsOnline) {
        this.toastPush(appIsOnline)
    },

    toastifyAppResponse(appResponse) {
        if (Object.keys(appResponse).length) return;
        this.toastPush(appResponse.message);
    },

    toastifyApiResponse(apiResponse) {
        if (this.$store.abgrid.apiRequest?.endpoint == "api/token") {
            return this.toastPush("Session was correclty initialized.");
        }
        this.toastPush(apiResponse.data.detail);
    }
})