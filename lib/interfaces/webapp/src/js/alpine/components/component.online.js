export default () => ({
    
    initOnline() {
        // Set initial online status
        this.$store.app.appIsOnline = navigator.onLine;
        
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
        this.$store.app.appIsOnline = online;
        this.$store.app.appIsOnline
            ? this.toastShowSuccess("online")
            : this.toastShowError("offline")
    }
});