export default () => ({
    isOnline: navigator.onLine,
    onlineStatusMessage: "",

    init() {
        // Set initial status
        this.updateStatus(navigator.onLine);

        // Listen for online/offline events
        window.addEventListener("online", () => {
            this.updateStatus(true);
        });

        window.addEventListener("offline", () => {
            this.updateStatus(false);
        });
    },

    updateStatus(online) {
        this.isOnline = online;
        this.onlineStatusMessage = online
            ? "Connected to the internet"
            : "No internet connection";

        // Your custom logic here
        if (online) {
            const page = this.$store.abgrid.navigateToPage("/")
            window.TextTrackList.navigateTo(page);
        } else {
            const page = this.$store.abgrid.navigateToPage("/notify")
            window.TextTrackList.navigateTo(page);
        }
    }
});