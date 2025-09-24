/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { downloadLink } from "../usables/use.download.link.js";

export default () => ({

    init() {
        // Lock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = true);

        // Store data from successful API call (since we landed here)
        this.$store.data.dataMultiStep.step3 = this.$store.api.apiResponse.data.detail;
    },

    multistepPDFSpinner: false,

    multistepPDFFileWasDownloaded: false,

    multistepDownloadLinkFactoryPDF() {
        return this.$store.app.appIsElectron
            // Electron app
            ? {
                    async ["@click.prevent"]() {
                        // Prevent multiple clicks
                        if (this.$store.api.apiRequestIsPending) return;
                        this.$store.app.appMagicButtonIsLocked = true;
                        this.$store.api.apiRequestIsPending = true;
                        const data = this.$store.data.dataMultiStep.step3
                        this.multistepPDFSpinner = true;
                        const response = await window.electronAPI.generateReport(data, "pdf");
                        response && this.toastifyReportGeneration(response);
                        this.multistepPDFSpinner = false;
                        this.$store.api.apiRequestIsPending = false;
                        this.$store.app.appMagicButtonIsLocked = response.status !== 200;
                    }
                }
            // Web app
            : {
                    ["@click.prevent"]() {
                        // Prevent multiple clicks
                        if (this.$store.api.apiRequestIsPending) return;
                        this.$store.app.appMagicButtonIsLocked = true;
                        this.$store.api.apiRequestIsPending = true;
                        const data = this.$store.data.dataMultiStep.step3
                        const type = "text/html";
                        const fileExtension = "html";
                        this.multistepPDFSpinner = true;
                        const filename = `abgrid-report.${fileExtension}`
                        const blob = new Blob([data], { type });
                        downloadLink(blob, filename)
                            .then(() => {
                                this.toastShowSuccess("download_success");
                                this.$store.app.appMagicButtonIsLocked = false;
                            })
                            .catch(({ message }) => this.toastShowError(message))
                            .finally(() => {
                                this.multistepPDFSpinner = false;
                                this.$store.api.apiRequestIsPending = false;
                            });
                    }
                }
    },

    magicButton: {

        ["label"]: "next",

        ["action"]() {
            this.navigationGoTo("/");
        }
    }
});
