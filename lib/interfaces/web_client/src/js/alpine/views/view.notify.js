export default () => ({

    templateGroup: {

        ["x-if"]() {
            return this.$store.abgrid.apiResponse?.statusCode < 400
                && this.$store.abgrid.apiRequest?.endpoint == "api/group";
        },

    },

    templateReport: {
        ["x-if"]() {
            return this.$store.abgrid.apiResponse?.statusCode < 400
                && this.$store.abgrid.apiRequest?.endpoint == "api/report";
        },

    },

    templateApiError: {
        ["x-if"]() {
            return this.$store.abgrid.apiResponse?.statusCode >= 400;
        },
    },

    templateApiErrorEndpoint: {
        ["x-text"]() {
            return this.$store.abgrid.apiRequest.endpoint == "api/group"
                ? "Creazione del file di gruppo"
                : "Creazione report";
        }
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
