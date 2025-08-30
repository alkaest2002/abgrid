/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { downloadLink } from "../usables/use.download.link.js";

export default () => ({

    init() {
        // Lock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = true);
    },

    notifyReportPDFSpinner: false,
    
    notifyReportJSONSpinner: false,

    notifyReportDownloadLinkFactory(typeOfData, spinner) {
        return this.$store.app.appIsElectron
            // Electron app
            ? {
                    async ["@click.prevent"]() {
                        this.$store.app.appMagicButtonIsLocked = true;
                        this.$store.api.apiRequestIsPending = true;
                        const data = typeOfData == "json"
                            ? JSON.stringify(this.$store.api.apiResponse?.data?.detail?.report_json || "{}")
                            : this.$store.api.apiResponse?.data?.detail?.report_html || "";
                        spinner = true;
                        const response = await window.electronAPI.generateReport(data, typeOfData);
                        response && this.toastifyReportGeneration(response);
                        spinner = false;
                        this.$store.app.appMagicButtonIsLocked = response.status === 200;
                        this.$store.api.apiRequestIsPending = false;
                    }
                }
            // Web app
            : {
                    ["@click.prevent"]() {
                        this.$store.app.appMagicButtonIsLocked = true;
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
                        const filename = `abgrid-report.${fileExtension}`
                        const blob = new Blob([data], { type });
                        downloadLink(blob, filename)
                            .then(() => {
                                this.toastShowSuccess("download_success");
                                this.$store.app.appMagicButtonIsLocked = false;
                            })
                            .catch(({ message }) => this.toastShowError(message))
                            .finally(() => {
                                spinner = false;
                                this.$store.api.apiRequestIsPending = false;
                            });
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
