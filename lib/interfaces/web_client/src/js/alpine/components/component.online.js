export default () => ({
    isOnline: navigator.onLine,
    onlineStatusMessage: "",

    init() {
        // Set initial status
        this.updateStatus(navigator.onLine);
        // Listen for online event
        window.addEventListener("online", () => {
            this.updateStatus(true);
        });
        // Listen for offline event
        window.addEventListener("offline", () => {
            this.updateStatus(false);
        });
    },

    updateStatus(online) {
        this.isOnline = online;
        this.onlineStatusMessage = online
            ? "Connected to the internet"
            : "No internet connection";
        if (online) {
           this.$store.abgrid.navigateTo("/")
        } else {
           this.$store.abgrid.navigateTo("notify")
        }
    }
});