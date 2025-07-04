export default () => ({

    lastVisited: null,

    navigateTo(page) {
        this.lastVisited = window.location.href;
        const pageToNavigateTo = page == "/"
            ? page
            : `/pages/${this.$store.abgrid.language}.${page}.html`
        window.Taxi.navigateTo(pageToNavigateTo)
    },

})