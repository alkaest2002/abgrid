/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
export default () => ({

    init() {
        // Unlock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = false);
    },

    get notifyErrorYaml() {
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
