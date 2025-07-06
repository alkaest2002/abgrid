export default () => ({

    magicButton: {

        label: "prev",

        ["action"]() {
            // Handle scenario where last page was report
            if (this.navigationLastVisited.includes("generate.report"))
                return this.navigateTo("/");
            this.navigateTo("navigationLastVisited");
        }
    }
});
