export default () => ({

    magicButton: {

        label: "next",

        ["action"]() {
            this.navigationGoTo("notify");
        }
    }
});
