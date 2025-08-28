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

    dropzoneDataShowWithSociogram: isSingleStepReport,

    dropzoneDataApiEndpoint: isSingleStepReport ? "api/report" : "api/report/step_1",

    dropzoneDataGoTo: isSingleStepReport ? "notify.report" : "multistep.sociogram",

    dropzoneDataTextareaContainer: {
        ["@textarea:input"]({ detail }) {
            // Save YAML data to store
            this.$store.data.dataYAML = detail;
        }
    },

    dropzoneDataDownloadLink: {
        ["@click.prevent"]() {
            // Do nothing if api request is pending
            if (this.$store.api.apiRequestIsPending) return;
            // Trigger download via a fake link
            this.$nextTick(() => {
                const groupId = this.$store.data.dataYAML.match(/group:\s*(?<id>\d+)/)?.groups?.id ?? '1';
                const blob = new Blob([this.$store.data.dataYAML], { type: 'application/x-yaml' });
                const url = URL.createObjectURL(blob);
                const link = Object.assign(document.createElement('a'), {
                    href: url,
                    download: `group_file_g${groupId}.yaml`,
                    style: { display: 'none' }
                });
                document.body.appendChild(link);
                link.click();
                queueMicrotask(() => {
                    document.body.removeChild(link);
                    URL.revokeObjectURL(url);
                });
            });
        }
    },

    dropzoneDataResetLink: {
        ["@click.prevent"]() {
            // Do nothing if api request is pending
            if (this.$store.api.apiRequestIsPending) return;
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
                    endpoint: this.dropzoneDataApiEndpoint,
                    method: "POST",
                    queryParams: {
                        "language": this.$store.app.appLanguage,
                        with_sociogram: this.dropzoneDataWithSociogram
                    },
                    bodyData: JSON.parse(JSON.stringify(convertYAMLToJSON))
                };
                // Make api request to server
                const { statusCode, data: { detail } } = await this.apiProcessRequest(apiRequest);
                // On api success
                if (statusCode == 200) {
                    // If generation of report is multi-step
                    if (!isSingleStepReport)
                        // Save api response to store
                        this.$store.data.dataMultiStep.step1 = detail;
                    // Navigate to appropriate page
                    this.navigationGoTo(this.dropzoneDataGoTo)
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
                } else {
                    this.navigationGoTo("notify.error.api");
                }
            }
        }
    },
});
