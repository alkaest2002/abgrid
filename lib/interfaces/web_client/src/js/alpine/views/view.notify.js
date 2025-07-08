export default () => ({

    templateReport: {
        ["x-if"]() {
            return this.$store.abgrid.apiResponse?.statusCode < 400
                && this.$store.abgrid.apiRequest?.endpoint == "api/report";
        },

    },

    templateAppError: {
        ["x-if"]() {
            return this.$store.abgrid.appResponse?.statusCode >= 400
        },

    },

    templateApiError: {
        ["x-if"]() {
            return this.$store.abgrid.apiResponse?.statusCode >= 400;
        },
    },

    magicButton: {

        label: "prev",

        ["action"]() {
            // Handle scenario where last page was report
            if (this.navigationLastVisited.includes("report"))
                return this.navigationGoTo("/");
            this.navigationGoTo("navigationLastVisited");
        }
    }
});
