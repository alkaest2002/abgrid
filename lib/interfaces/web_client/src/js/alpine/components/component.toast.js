export default () => ({
    init() {
        this.$watch("$store.abgrid.appIsOnline", (appIsOnline) => this.toastifyAppIsOnline(appIsOnline));
        this.$watch("$store.abgrid.apiData", (apiData) => this.toastifyApiData(apiData));
        this.$watch("$store.abgrid.appData", (appData) => this.toastifyAppData(appData));
    },

    toastifyAppIsOnline(appIsOnline) {
        console.log(appIsOnline)
    },

    toastifyApiData(apiData) {
        console.log(apiData)
    },

    toastifyAppData(appData) {
        console.log(appData)
    }
})