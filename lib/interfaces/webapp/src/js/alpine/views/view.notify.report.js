export default () => ({

    notifyShowFilePDFSpinner: false,
    notifyShowFileJSONSpinner: false,

    notifyReportDownloadLinkFactory(typeOfData, spinner) {
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

    magicButton: {

        ["label"]: "home",

        ["action"]() {
            this.navigationGoTo("/");
        }
    }
});
