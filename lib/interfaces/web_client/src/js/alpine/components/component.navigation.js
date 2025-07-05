export default () => ({

    lastVisited: "/",

    navigateTo(page) {
        const pageToNavigateTo = page == "/"
            ? page
            : page == "lastVisited"
                ? this.lastVisited
                : `/pages/${this.$store.abgrid.appLanguage}.${page}.html`;
        this.lastVisited = window.location.href;
        window.Taxi.navigateTo(pageToNavigateTo);
    },

})