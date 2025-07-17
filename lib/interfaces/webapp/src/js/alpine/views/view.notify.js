export default () => ({

    destroy() {
        // reset api and app Responses
        this.$store.api.apiResponse = {};
        this.$store.data.dataYAMLError = {};
    },

    notifyShowFilePDFSpinner: false,
    notifyShowFileJSONSpinner: false,

    get notifyPydanticErrors() {
        return this.$store.api.apiResponse?.data?.detail;
    },

    get notifyYamlErrors() {
        const lines = Object
            .values(this.$store.data.dataYAMLError?.linePos || [])
            .map((obj) => obj.line);
        return lines.filter((x, index) => lines.indexOf(x) === index);
    },

    notifyDownloadLinkFactory(typeOfData, spinner) {
        return this.$store.app.appIsElectron
            // Electron app
            ?
                {
                    async ["@click.prevent"]() {
                        const data = typeOfData == "json"
                            ? JSON.stringify(this.$store.api.apiResponse?.data?.detail?.report_json || "{}")
                            : this.$store.api.apiResponse?.data?.detail?.report_html || "";
                        spinner = true;
                        const response = await window.electronAPI.generateReport(data, typeOfData);
                        response && this.toastifyReportGeneration(response);
                        spinner = false;
                    }
                }
            // Web app
            : 
                {
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
                }
    },

    templateReport: {
        ["x-if"]() {
            return this.$store.api.apiResponse?.statusCode < 400
                && this.$store.api.apiRequest?.endpoint == "api/report";
        },
    },

    templateAppError: {
        ["x-if"]() {
            return Object.keys(this.$store.data.dataYAMLError).length > 0;
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
            const { endpoint = null } = this.$store.api.apiRequest;
            const { statusCode = 400 } = this.$store.api.apiResponse;
            // Handle scenario where last operation was a succesful report generation
            if (this.navigationLastVisited.includes("dropzone") 
                    && endpoint === "api/report"
                    && statusCode == 200
                )
                return this.navigationGoTo("/");
            this.navigationGoTo("navigationLastVisited");
        }
    }
});
