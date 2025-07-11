export default () => ({

    initNavigation() {
    },

    navigationLastVisited: "/",

    navigationGoTo(page) {
        // Determine page to navigate to
        const pageTonavigationGoTo = page == "/"
            ? page
            : page == "navigationLastVisited"
                ? this.navigationLastVisited
                : `/pages/${this.$store.abgrid.appLanguage}.${page}.html`;
        // Save current location
        this.navigationLastVisited = window.location.href;
        // Navigate to page
        window.Taxi.navigateTo(pageTonavigationGoTo);
    },

})