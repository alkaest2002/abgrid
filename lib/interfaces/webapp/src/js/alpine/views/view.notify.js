export default () => ({

    destroy() {
        // reset api and app Responses
        this.$store.api.apiResponse = {};
        this.$store.app.appResponse = {};
    },

    notifyShowFilePDFSpinner: false,
    notifyShowFileJSONSpinner: false,

    get notifyPydanticErrors() {
        return this.$store.api.apiResponse?.data?.detail;
    },

    get notifyYamlErrors() {
        const lines = Object
            .values(this.$store.app.appResponse.data?.detail?.linePos || [])
            .map((obj) => obj.line);
        return lines.filter((x, index) => lines.indexOf(x) === index);
    },

    notifyDownloadLinkFactory: (typeOfData, spinner) => ({
        ["@click.prevent"]() {
            const data = typeOfData == "json"
                ? JSON.stringify(this.$store.api.apiResponse?.data?.detail?.report_json || "{}")
                : this.$store.api.apiResponse?.data?.detail?.report_html || "";
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
            return this.$store.api.apiResponse?.statusCode < 400
                && this.$store.api.apiRequest?.endpoint == "api/report";
        },
    },

    templateAppError: {
        ["x-if"]() {
            return this.$store.app.appResponse?.statusCode >= 400
        },
    },

    templateApiError: {
        ["x-if"]() {
            return this.$store.api.apiResponse?.statusCode >= 400;
        },
    },

    magicButton: {

        ["label"]() {
            return this.$store.api.apiResponse?.data?.detail?.report_json
                ? "home"
                : "prev"
        },

        ["action"]() {
            // Extract info from api request and response
            const { apiEnpoint = null } = this.$store.api.apiRequest;
            const { statusCode = 400 } = this.$store.api.apiResponse;
            // Handle scenario where last operation was a succesful report generation
            if (this.navigationLastVisited.includes("dropzone") 
                    && apiEnpoint === "api/report"
                    && statusCode == 200
                )
                return this.navigationGoTo("/");
            this.navigationGoTo("navigationLastVisited");
        }
    }
});
