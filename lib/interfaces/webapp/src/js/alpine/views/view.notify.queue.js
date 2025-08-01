export default () => ({

    init() {
        // Unlock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = false);
    },

    destroy() {},

    magicButton: {

        ["label"]: "home",

        ["action"]() {
            this.navigationGoTo("home");
        }
    }
});
