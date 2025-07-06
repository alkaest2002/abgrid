export default () => ({

    magicButton: {

        label: "prev",

        ["action"]() {
            // Handle scenario where last page was report
            if (this.navigationLastVisited.includes("generate.report"))
                return this.navigationGoTo("/");
            this.navigationGoTo("navigationLastVisited");
        }
    }
});
