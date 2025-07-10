export default () => ({

    init() {
        const lines = Object
            .values(this.$store.abgrid.appResponse.data?.detail?.linePos || [])
            .map((obj) => obj.line);
        this.notifyYamlUniqueLines = lines.filter((x, index) => lines.indexOf(x) === index);
    },

    notifyYamlUniqueLines: []

})