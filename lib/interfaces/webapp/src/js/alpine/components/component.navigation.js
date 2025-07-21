export default () => ({

    initNavigation() {},

    navigationLastVisited: "/",

    navigationGoTo(page) {
        // Determine page to navigate to
        const finalDestination = page == "/"
            ? page
            : page == "navigationLastVisited"
                ? this.navigationLastVisited
                : `/pages/${this.$store.app.appLanguage}.${page}.html`;
        
        // Save current location
        this.navigationLastVisited = window.location.href;
        
        // Navigate to page
        window.Taxi.navigateTo(finalDestination);
    },

})