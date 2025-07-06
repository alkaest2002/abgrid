export default () => ({
    
    initToast() {
        // Log
        console.log("initToast")
        // Watch store props
        this.$watch("$store.abgrid.appIsOnline", (appIsOnline) => this.toastifyAppIsOnline(appIsOnline));
        this.$watch("$store.abgrid.appResponse", (appResponse) => this.toastifyAppResponse(appResponse));
        this.$watch("$store.abgrid.apiResponse", (apiResponse) => this.toastifyApiResponse(apiResponse));
    },

    toastifyAppIsOnline(appIsOnline) {
        console.log(`app status is ${appIsOnline}`)
    },

    toastifyAppResponse(appResponse) {
        if (Object.keys(appResponse).length) return;
        console.log(appResponse)
    },

    toastifyApiResponse(apiResponse) {
        console.log(apiResponse)
    }
})