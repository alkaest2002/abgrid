import { parse } from "yaml";
import  { readFileWithLineLimit } from "../usables/use.text.reader"

export default () => ({

    init() {
        this.$store.abgrid.magicButtonIsLocked = !this.$store.abgrid.reportDataJSON;
    },

    dropzoneWithSociogram: true,

    async dropzoneProcessFile(file) {
        try {
            // Check if it's a YAML file
            if (file.type === "application/x-yaml" && file.name.endsWith(".yaml")) {
                try {
                    // Read file with 300 line limit
                    const limitedContent = await readFileWithLineLimit(file, 300);
                    // Convert YAML to JSON
                    const jsonReportData = parse(limitedContent);
                    // Get actual keys from jsonReportData
                    const jsonReportDataKeys = Object.keys(jsonReportData);
                    // Set expected keys
                    const expectedKeys = ["project_title", "question_a", "question_b", "group", "choices_a", "choices_b"];
                    // If actual and expected keys are different
                    if (JSON.stringify(jsonReportDataKeys.sort()) !== JSON.stringify(expectedKeys.sort())) {
                        // Handle error directly
                        return this.toastPush(400, this.$t("errors.file_invalid_keys"));
                    }
                    // Save filename to store
                    this.$store.abgrid.reportDataFilename = file.name;
                    // Save JSON report data to store
                    this.$store.abgrid.reportDataJSON = jsonReportData;
                    // Save YAML report data to store
                    this.$store.abgrid.reportDataYAML = limitedContent;
                    // Notify success
                    this.toastPush(200, this.$t("success.successful_operation"));
                } catch (error) {
                    // Check if it's a line limit error
                    if (error.message.includes('exceeds_size_limit')) {
                        this.toastPush(400, this.$t("errors.file_exceeds_size_limit"));
                    } else {
                        this.toastPush(400, this.$t("errors.file_load_failure"));
                    }
                }
            } else {
                this.toastPush(400, this.$t("errors.file_invalid_type"));
            }
        } catch (error) {
            this.toastPush(400, this.$t("errors.file_load_failure"));
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
        },

        ["@textarea:input"]({ detail }) {
            this.$store.abgrid.reportDataYAML = detail;
        }
    },

    dropzoneDownloadLink: {
        
        ["@click.prevent"]() {
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

        async ["action"]() {
            try {
                // Save parse yaml data into store
                this.$store.abgrid.reportDataJSON = parse(this.$store.abgrid.reportDataYAML);
                
                this.$store.abgrid.apiRequest = {
                    endpoint: "api/report",
                    method: "POST",
                    queryParams: {"language": "it", with_sociogram: this.dropzoneWithSociogram },
                    bodyData: JSON.parse(JSON.stringify(this.$store.abgrid.reportDataJSON))
                };
                // Call server
                await this.apiHandleRequest(this.$store.abgrid.apiRequest);
            } catch (error) {
                console.log(error)
                if ("name" in error && error.name == "YAMLParseError") {
                    console.log(Object.keys(error))
                    // Set app response
                    this.$store.abgrid.appResponse = {
                        statusCode: 400,
                        error: error.code,
                        data: { detail: error }
                    };
                }
            } finally {
                // Go to notify
                this.navigationGoTo("notify");
            }
        }
    }
});
