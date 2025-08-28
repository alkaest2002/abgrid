/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { downloadLink } from "../usables/use.download.link.js";

export default () => ({

    init() {
        // Unlock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = false);
    },

    multistepPDFSpinner: false,


    multistepDownloadLinkFactoryPDF() {
        return this.$store.app.appIsElectron
            // Electron app
            ? {
                    async ["@click.prevent"]() {
                        const data = this.$store.data.dataMultiStep.step3
                        this.multistepPDFSpinner = true;
                        const response = await window.electronAPI.generateReport(data, "pdf");
                        response && this.toastifyReportGeneration(response);
                        this.multistepPDFSpinner = false;
                    }
                }
            // Web app
            : {
                    ["@click.prevent"]() {
                        const data = this.$store.data.dataMultiStep.step3
                        const type = "text/html";
                        const fileExtension = "html";
                        this.multistepPDFSpinner = true;
                        const filename = `abgrid-report.${fileExtension}`
                        const blob = new Blob([data], { type });
                        downloadLink(blob, filename)
                            .then(() => this.toastShowSuccess("download_success"))
                            .catch(() => this.toastShowError("download_failure"));
                        this.multistepPDFSpinner = false;
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
