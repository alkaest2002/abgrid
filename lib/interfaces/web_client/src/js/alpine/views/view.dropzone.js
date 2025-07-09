import { parse } from "yaml";

export default () => ({

    init() {
        this.$store.abgrid.magicButtonIsLocked = !this.$store.abgrid.reportDataJSON;
    },

    dropzoneUpdateYAML() {
        this.$store.abgrid.reportDataYAML = this.$refs.YAMLtextArea.value;
    },

    dropzoneProcessFile(file) {
        try {
            // Check if it's a YAML file
            if (file.type === "application/x-yaml" && file.name.endsWith(".yaml")) {
                const reader = new FileReader();
                reader.onload = (evt) => {
                    try {
                        // Convert YAML to JSON
                        const jsonReportData = parse(evt.target.result);
                        // Get actual keys from jsonReportData
                        const jsonReportDataKeys = Object.keys(jsonReportData);
                        // Set expected keys
                        const expectedKeys = ["project_title", "question_a", "question_b", "group", "choices_a", "choices_b"];
                        // If actual and expected keys are different
                        if (JSON.stringify(jsonReportDataKeys.sort()) !== JSON.stringify(expectedKeys.sort())) {
                            // Handle error directly
                            return this.toastPush(400, this.$t("errors.yaml_invalid"));
                        }
                        // Save filename to store
                        this.$store.abgrid.reportDataFilename = file.name;
                        // Save JSON report data to store
                        this.$store.abgrid.reportDataJSON = jsonReportData;
                        // Save YAML report data to store
                        this.$store.abgrid.reportDataYAML = evt.target.result;
                        // Scroll text area to top
                        this.$refs.YAMLtextArea.scrollTop = 0;
                        // Notify success
                        this.toastPush(200, this.$t("success.successful_operation"));
                    } catch (error) {
                        this.toastPush(400, this.$t("errors.yaml_load_failure"));
                    }
                };
                reader.readAsText(file);
            } else {
                this.toastPush(400, this.$t("errors.invalid_file_type"));
            }
        } catch (error) {
            // This only catches synchronous errors (like YAML.parse errors that happen immediately)
            this.toastPush(400, this.$t("errors.yaml_load_failure"));
        }
    },

    dropzone: {
        
        ["@click"]({ altKey }) {
            // Do nothing if alt key was pressed
            if (!altKey) return;
            // Create file input element
            const fileInput = document.createElement("input");
            fileInput.type = "file";
            fileInput.accept = ".yaml, application/x-yaml";
            fileInput.style.display = "none";
            // Cleanup function
            const cleanup = () => {
                if (document.body.contains(fileInput)) {
                    document.body.removeChild(fileInput);
                }
            };
            // Handle file selection
            fileInput.onchange = (event) => {
                if (event.target.files && event.target.files.length > 0) {
                    this.dropzoneProcessFile(event.target.files[0]);
                }
                cleanup();
            };
            // Handle cancel (when user closes dialog without selecting)
            fileInput.oncancel = cleanup;
            // Add to DOM and trigger click
            document.body.appendChild(fileInput);
            fileInput.click();
        },

        ["@dragover.prevent.stop"]() {
            // Prevent default drag behavior
        },

        ["@drop.prevent.stop"]($event) {
            // Check if files were dropped
            if ($event.dataTransfer.files && $event.dataTransfer.files.length > 0) {
                this.dropzoneProcessFile($event.dataTransfer.files[0]);
            }
        }
    },

    dropzoneDownloadLink: {
        
        ["@click.prevent"]() {
            // Update yaml data
            this.dropzoneUpdateYAML();
            // Then trigger download via a fake link
            this.$nextTick(() => {
                const link = document.createElement("a");
                link.href = `data:application/x-yaml;base64,${btoa(this.$store.abgrid.reportDataYAML)}`;
                link.download = this.$store.abgrid.reportDataJSON?.group
                    ? `group_file_g${this.$store.abgrid.reportDataJSON.group}.yaml`
                    : 'group_file_g1.yaml';
                link.click();
            });
        }
    },

    dropzoneResetLink: {
        ["@click.prevent"]() {
            // Cancel report data
            this.$store.abgrid.reportDataFilename = "";
            this.$store.abgrid.reportDataYAML = "";
            this.$store.abgrid.reportDataJSON = {};
        }
    },

    magicButton: {

        label: "next",

        ["action"]() {
            try {
                // Update yaml data
                this.dropzoneUpdateYAML();
                // Save parse yaml data into store
                this.$store.abgrid.reportDataJSON = parse(this.$store.abgrid.reportDataYAML);
            } catch (error) {
                // Set app response
                this.$store.abgrid.appResponse = {
                    statusCode: 400,
                    error,
                    data: { detail: null }
                };
                // Go to notify
                this.navigationGoTo("notify");
            }
        }
    }
});
