export default () => ({
    
    init() {
        // Set initial online status
        this.$store.abgrid.appIsOnline = navigator.onLine;
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
        if (online && !this.$store.abgrid.appIsOnline) {
            this.$store.abgrid.appIsOnline = online;
        }
        // If app is offline
        if (!online) {
            this.$store.abgrid.appIsOnline = online;
        }
    }
});