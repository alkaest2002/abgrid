export default () => ({

    magicButton: {

        label: "prev",

        ["action"]() {
            this.navigateTo("lastVisited");
        }
    }
});
