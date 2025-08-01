import { parse } from "yaml";

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

    dropzoneDataTextareaContainer: {
        ["@textarea:input"]({ detail }) {
            // Save YAML data to store
            this.$store.data.dataYAML = detail;
            // Reset JSON if detail is void
            if (!detail) this.$store.data.dataJSON = {};
        }
    },

    dropzoneDataDownloadLink: {
        ["@click.prevent"]() {
            // Trigger download via a fake link
            this.$nextTick(() => {
                const link = document.createElement("a");
                link.href = `data:application/x-yaml;base64,${btoa(this.$store.data.dataYAML)}`;
                link.download = this.$store.data.dataJSON?.group
                    ? `group_file_g${this.$store.data.dataJSON.group}.yaml`
                    : 'group_file_g1.yaml';
                // Append to body, click, then clean up with delay
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

                // Save converted JSON to store
                this.$store.data.dataJSON = convertYAMLToJSON;

                // Create api request
                const apiRequest = {
                    endpoint: "api/report",
                    method: "POST",
                    queryParams: { 
                        "language": this.$store.app.appLanguage, 
                        with_sociogram: this.dropzoneDataWithSociogram 
                    },
                    bodyData: JSON.parse(JSON.stringify(this.$store.data.dataJSON))
                };
                // Make api request to server
                const { statusCode } = await this.apiHandleRequest(apiRequest);

                // On api success
                if (statusCode == 200) {
                    // Navigate to report notification page
                    this.navigationGoTo("notify.report")
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
                    // Reset JSON content
                    this.$store.data.dataJSON = {};
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
