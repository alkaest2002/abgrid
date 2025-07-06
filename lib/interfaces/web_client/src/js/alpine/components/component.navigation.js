export default () => ({

    initNavigation() {
        // Log
        console.log("initNavigation")
    },

    navigationLastVisited: "/",

    navigationGoTo(page) {
        // return home it meta key has been pressed
        if (this.magicButtonMetaKeyIsPressed)
            return window.Taxi.navigateTo("/");
        // Determine page to navigate to
        const pageTonavigationGoTo = page == "/"
            ? page
            : page == "navigationLastVisited"
                ? this.navigationLastVisited
                : `/pages/${this.$store.abgrid.appLanguage}.${page}.html`;
        this.navigationLastVisited = window.location.href;
        window.Taxi.navigateTo(pageTonavigationGoTo);
    },

})