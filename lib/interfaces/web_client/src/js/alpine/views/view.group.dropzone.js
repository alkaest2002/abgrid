import YAML from "yaml";

export default () => ({

    init() {
        this.$store.abgrid.magicButtonIsLocked = !this.$store.abgrid.reportData;
    },

    // Abstracted common file processing logic
    processFile(file) {
        try {
            // Store filename
            this.$store.abgrid.reportDataFilename = file.name;
            // Check if it's a YAML file
            if (file.type === "application/x-yaml" && file.name.endsWith(".yaml")) {
                const reader = new FileReader();
                reader.onload = (evt) => {
                    try {
                        // Convert YAML to JSON
                        const jsonReportData = YAML.parse(evt.target.result);
                        // Get keys of jsonReportData
                        const jsonReportDataKeys = Object.keys(jsonReportData);
                        // Set expected keys
                        const expectedKeys = ["project_title", "question_a", "question_b", "group", "choices_a", "choices_b"];
                        // If keys are not the same
                        if (JSON.stringify(jsonReportDataKeys.sort()) !== JSON.stringify(expectedKeys.sort())) {
                            // Handle error directly
                            return this.toastPush(400, this.$t("errors.yaml_invalid"));
                        }
                        // Save JSON report data to store
                        this.$store.abgrid.reportData = jsonReportData;
                        // Notify success
                        this.toastPush(200, this.$t("ops.successful_operation"));
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

        ["@click"]() {
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
                    this.processFile(event.target.files[0]);
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
                this.processFile($event.dataTransfer.files[0]);
            }
        }
    },

    magicButton: {

        label: "next",

        ["action"]() {
            this.navigationGoTo("report");
        }
    }
});
