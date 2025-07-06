export default () => ({

    magicButton: {

        label: "prev",

        ["action"]() {
            // Handle metakey
            if (this.magicButtonMetaKeyIsPressed)
                return this.navigateTo("/");
            // Handle scenario where last page was report
            if (this.navigationLastVisited.includes("generate.report"))
                return this.navigateTo("/");
            this.navigateTo("navigationLastVisited");
        }
    }
});
