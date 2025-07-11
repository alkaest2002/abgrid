export default () => ({
    
    initOnline() {
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
        this.$store.abgrid.appIsOnline = online;
    }
});