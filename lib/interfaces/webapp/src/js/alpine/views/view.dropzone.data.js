/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { parse } from "yaml";

const isSingleStepReport = import.meta.env.VITE_TYPE_OF_REPORT == "single_step";

export default () => ({

    init() {
        // Unlock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = false);

        // Watch for changes in store dataYAML
        this.$watch("$store.data.dataYAML", (value) => {
            this.$store.app.appMagicButtonIsLocked = !value;
        });
    },

    dropzoneDataWithSociogram: true,

    showDropzoneDataWithSociogram: isSingleStepReport,

    apiEndpoint: isSingleStepReport ? "api/report" : "api/report/step_1",

    goTo: isSingleStepReport ? "notify.report" : "report.step_2",

    dropzoneDataTextareaContainer: {
        ["@textarea:input"]({ detail }) {
            // Save YAML data to store
            this.$store.data.dataYAML = detail;
        }
    },

    dropzoneDataDownloadLink: {
        ["@click.prevent"]() {
            // Trigger download via a fake link
            this.$nextTick(() => {
                const match = this.$store.data.dataYAML.match(/group:\s*(\d+)/);
                const groupId = match ? match[1] : 1;
                const link = document.createElement("a");
                link.href = `data:application/x-yaml;base64,${btoa(this.$store.data.dataYAML)}`;
                link.download = `group_file_g${groupId}.yaml`;
                document.body.appendChild(link);
                link.click();
                setTimeout(() => document.body.removeChild(link), 100);
            });
        }
    },

    dropzoneDataResetLink: {
        ["@click.prevent"]() {
            // Wipe data
            this.$store.data.wipeState();
            // Go to dropzone empty
            this.navigationGoTo("dropzone.empty");
        }
    },

    magicButton: {

        label: "next",

        async ["action"]() {
            try {
                // Convert YAML to JSON
                const convertYAMLToJSON = parse(this.$store.data.dataYAML);

                // Create api request
                const apiRequest = {
                    endpoint: this.apiEndpoint,
                    method: "POST",
                    queryParams: { 
                        "language": this.$store.app.appLanguage, 
                        with_sociogram: this.dropzoneDataWithSociogram 
                    },
                    bodyData: JSON.parse(JSON.stringify(convertYAMLToJSON))
                };
                // Make api request to server
                const { statusCode } = await this.apiProcessRequest(apiRequest);

                // On api success
                if (statusCode == 200) {
                    // Navigate to appropriate page
                    this.navigationGoTo(this.goTo)
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
                // YAML error
                if ("name" in error && error.name == "YAMLParseError") {
                    // Save YAML error to store
                    this.$store.data.dataYAMLError = error;
                    // Toast error
                    this.toastShowError("file_invalid_yaml");
                    // Go to notify
                    this.navigationGoTo("notify.error.yaml");
                // Api error
                } else{
                    this.navigationGoTo("notify.error.api");
                }
            }
        }
    },
});
