export default () => ({
    
    initOnline() {
        // Log
        console.log("initOnline")
        // Set initial online status
        this.$store.abgrid.appIsOnline = navigator.onLine;
        // Listen for online event
        window.addEventListener("online", 
            () => this.onlineUpdateStatus(true)
        );
        // Listen for offline event
        window.addEventListener("offline", 
            () => this.onlineUpdateStatus(false)
        );
    },

    onlineUpdateStatus(online) {
        // If app returns on-line after being offline
        if (online && !this.$store.abgrid.appIsOnline) {
            this.$store.abgrid.appIsOnline = true;
        }
        // If app is offline
        if (!online) {
            this.$store.abgrid.appIsOnline = false;
        }
    }
});