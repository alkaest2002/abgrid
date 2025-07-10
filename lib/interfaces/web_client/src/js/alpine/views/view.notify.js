export default () => ({

    destroy() {
        // reset api and app Responses
        this.$store.abgrid.apiResponse = {};
        this.$store.abgrid.appResponse = {};
    },

    notifyShowFilePDFSpinner: false,
    notifyShowFileJSONSpinner: false,

    get notifyPydanticErrors() {
        return this.$store.abgrid.apiResponse?.data?.detail;
    },

    get notifyYamlErrors() {
        const lines = Object
            .values(this.$store.abgrid.appResponse.data?.detail?.linePos || [])
            .map((obj) => obj.line);
        return lines.filter((x, index) => lines.indexOf(x) === index);
    },

    notifyDownloadLinkFactory: (typeOfData, spinner) => ({
        ["@click.prevent"]() {
            const data = typeOfData == "json"
                ? JSON.stringify(this.$store.abgrid.apiResponse?.data?.detail?.report_json || "{}")
                : this.$store.abgrid.apiResponse?.data?.detail?.report_html || "";
            const type = typeOfData == "json"
                ? "application/json"
                : "text/html";
            const fileExtension = typeOfData == "json"
                ? "json"
                : "html";
            spinner = true;
            const blob = new Blob([data], { type });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `abgrid-report.${fileExtension}`;
            a.click();
            URL.revokeObjectURL(url);
            spinner = false;
        }
    }),

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

    notifyAppErrorList: {
        ["x-for"]: "errorLine in notifyYamlErrors"
    },

    templateApiError: {
        ["x-if"]() {
            return this.$store.abgrid.apiResponse?.statusCode >= 400;
        },
    },

    notifyApiErrorList: {
        ["x-for"]: "error in $store.abgrid.apiResponse?.data?.detail"
    },

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
