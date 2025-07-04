export default () => ({

    lastVisited: null,

    navigateTo(page) {
        const pageToNavigateTo = page == "/"
            ? page
            : page == "lastVisited"
                ? this.lastVisited
                : `/pages/${this.$store.abgrid.language}.${page}.html`;
        this.lastVisited = window.location.href;
        window.Taxi.navigateTo(pageToNavigateTo);
    },

})