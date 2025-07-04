export default () => ({

    magicButton: {

        label: "next",

        ["action"]() {
            this.navigateTo("generate.group");
        }
    }
});
