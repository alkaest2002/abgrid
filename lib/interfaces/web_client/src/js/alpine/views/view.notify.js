export default () => ({

    init() {
    },

    destroy() {
        // reset api and app Responses
        this.$store.abgrid.apiResponse = {};
        this.$store.abgrid.appResponse = {};
    },

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

    notifyDownloadLinkFactory: (typeOfData) => ({
        ["@click.prevent"]() {
            console.log(typeOfData)
            const data = typeOfData == "json"
                ? JSON.stringify(this.$store.abgrid.apiResponse?.data?.detail?.report_json || "{}")
                : this.$store.abgrid.apiResponse?.data?.detail?.report_html || ""
            const type = typeOfData == "json"
                ? "application/json"
                : "text/html"
            const blob = new Blob([data], { type });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `abgrid-report.${typeOfData}`;
            a.click();
            URL.revokeObjectURL(url);
        }
    }),

    magicButton: {

        ["label"]() {
            return this.$store.abgrid.apiResponse?.data?.detail?.report_json
                ? "home"
                : "prev"
        },

        ["action"]() {
            // Handle scenario where last page was report
            if (this.navigationLastVisited.includes("report"))
                return this.navigationGoTo("/");
            this.navigationGoTo("navigationLastVisited");
        }
    }
});
