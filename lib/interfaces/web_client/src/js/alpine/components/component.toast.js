export default () => ({
    
    initToast() {
        // Log
        console.log("initToast")
        // Watch store props
        this.$watch("$store.abgrid.appIsOnline", (appIsOnline) => this.toastifyAppIsOnline(appIsOnline));
        this.$watch("$store.abgrid.appData", (appData) => this.toastifyAppData(appData));
        this.$watch("$store.abgrid.apiData", (apiData) => this.toastifyApiData(apiData));
    },

    toastifyAppIsOnline(appIsOnline) {
        console.log(`app status is ${appIsOnline}`)
    },

    toastifyApiData(apiData) {
        console.log(apiData)
    },

    toastifyAppData(appData) {
        console.log(appData)
    }
})