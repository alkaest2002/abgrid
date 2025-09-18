/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { downloadLink } from "../usables/use.download.link.js";

export default () => ({

    init() {
        
        // Lock magic button
        this.$nextTick(() => {
            this.$store.app.appMagicButtonIsLocked = true;
        });

        // Store data from successful API call (since we landed here)
        this.$store.data.dataMultiStep.step2 = this.$store.api.apiResponse.data.detail;
    },

    multistepJSONSpinner: false,

    multistepDownloadLinkFactoryJSON() {
        return this.$store.app.appIsElectron
            // Electron app
            ? {
                    async ["@click.prevent"]() {
                        this.$store.app.appMagicButtonIsLocked = true;
                        this.$store.api.apiRequestIsPending = true;
                        const data = this.$store.data.dataMultiStep.step2.stringified_data
                        this.multistepJSONSpinner = true;
                        const response = await window.electronAPI.generateReport(data, "json");
                        response && this.toastifyReportGeneration(response);
                        this.multistepJSONSpinner = false;
                        this.$store.api.apiRequestIsPending = false;
                        this.$store.app.appMagicButtonIsLocked = response.status !== 200;
                    }
                }
            // Web app
            : {
                    ["@click.prevent"]() {
                        this.$store.app.appMagicButtonIsLocked = true;
                        this.$store.api.apiRequestIsPending = true;
                        const data = this.$store.data.dataMultiStep.step2.stringified_data
                        const type = "application/json";
                        const fileExtension = "json";
                        this.multistepJSONSpinner = true;
                        const filename = `abgrid-report.${fileExtension}`
                        const blob = new Blob([data], { type });
                        downloadLink(blob, filename)
                            .then(() => { 
                                this.toastShowSuccess("download_success");
                                this.$store.app.appMagicButtonIsLocked = false;
                            })
                            .catch(({ message }) => this.toastShowError(message))
                            .finally(() => {
                                this.multistepJSONSpinner = false;
                                this.$store.api.apiRequestIsPending = false;
                            });
                    }
                }
    },

    magicButton: {

        ["label"]: "next",

        async ["action"]() {
            // Get data to send
            const bodyData = JSON.parse(
                JSON.stringify(
                    this.$store.data.dataMultiStep.step2
                )
            )
            // Try api
            try {
                // Create api request
                const apiRequest = {
                    endpoint: "api/report/step_3",
                    method: "POST",
                    bodyData,
                    queryParams: { 
                        "language": this.$store.app.appLanguage, 
                    },
                };
                // Make api request to server
                const { statusCode, data: { detail }} = await this.apiProcessRequest(apiRequest);
                // On api success
                if (statusCode == 200) {
                    // Navigate to appropriate page
                    this.navigationGoTo("multistep.report")
                    // On api queue error
                } else if (statusCode == 429) {
                    // Navigate to queue notification page
                    this.navigationGoTo("notify.queue");
                    // On any other api error
                } else {
                    // Navigate to error api notification page
                    this.navigationGoTo("notify.error.api");
                }
            // On error
            } catch (error) {
                this.navigationGoTo("notify.error.api");
            }
        }
    }
});
