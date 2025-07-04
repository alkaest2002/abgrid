export default () => ({
    
    isOnline: null,

    init() {
        // Set initial online status
        this.isOnline = navigator.onLine;
        // Listen for online event
        window.addEventListener("online", 
            () => this.updateStatus(true)
        );
        // Listen for offline event
        window.addEventListener("offline", 
            () => this.updateStatus(false)
        );
    },

    updateStatus(online) {
        // If app returns on-line after being offline
        if (online && !this.isOnline) {
            this.isOnline = online;
            window.Taxi.navigateTo("/")
        }
        // If app is offline
        if (!online) {
            this.isOnline = online;
            const page = `/pages/${this.$store.abgrid.language}.notify.html`
            window.Taxi.navigateTo(page)
        }
    }
});