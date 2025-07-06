export default () => ({

    magicButton: {

        label: "prev",

        ["action"]() {
            // Handle metakey
            if (this.magicButtonMetaKeyIsPressed)
                return this.navigateTo("/");
            if (this.navigationLastVisited.includes("generate.report"))
                return this.navigateTo("/");
            this.navigateTo("navigationLastVisited");
        }
    }
});
