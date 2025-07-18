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

    async onlineUpdateStatus(online) {
        if (online) {
            await this.apiPokeServer();
        }
        this.$store.api.apiServerIsReachable = online
            ? this.$store.api.apiServerIsReachable
            : false;
        this.$store.app.appIsOnline = online;
        this.$store.app.appIsOnline
            ? this.toastShowSuccess("online")
            : this.toastShowError("offline");
    }
});