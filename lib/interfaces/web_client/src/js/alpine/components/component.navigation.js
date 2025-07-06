export default () => ({

    navigationLastVisited: "/",

    initNaviagation() {
        // Log
        console.log("initNaviagation")
    },

    navigateTo(page) {
        const pageToNavigateTo = page == "/"
            ? page
            : page == "navigationLastVisited"
                ? this.navigationLastVisited
                : `/pages/${this.$store.abgrid.appLanguage}.${page}.html`;
        this.navigationLastVisited = window.location.href;
        window.Taxi.navigateTo(pageToNavigateTo);
    },

})