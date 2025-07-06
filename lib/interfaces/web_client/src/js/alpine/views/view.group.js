export default () => ({

    magicButton: {

        label: "next",

        ["action"]() {
            this.magicButtonMetaKeyIsPressed
                ? this.navigateTo("/")
                : this.navigateTo("generate.report");
        }
    }
});
