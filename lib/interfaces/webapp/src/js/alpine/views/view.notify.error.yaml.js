export default () => ({

    destroy() {
        // Reset api and app Responses
        this.$store.api.apiResponse = {};
        this.$store.data.dataYAMLError = {};
    },

    get notifyYamlErrors() {
        const lines = Object
            .values(this.$store.data.dataYAMLError?.linePos || [])
            .map((obj) => obj.line);
        // Filter removes duplicates
        return lines.filter((x, index) => lines.indexOf(x) === index);
    },

    magicButton: {

        ["label"]: "prev",

        ["action"]() {
            this.navigationGoTo("dropzone.data");
        }
    }
});
