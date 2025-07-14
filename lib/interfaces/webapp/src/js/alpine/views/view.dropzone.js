import { parse } from "yaml";
import  { readFileWithLineLimit } from "../usables/use.text.reader"

export default () => ({

    init() {
        this.$store.app.appMagicButtonIsLocked = 
            Object.keys(this.$store.data.dataJSON).length == 0;
    },

    dropzoneWithSociogram: true,

    async dropzoneProcessFile(file) {
        try {
            
            // Check file size first (100KB = 100 * 1024 bytes)
            const maxFileSize = 100 * 1024;
            if (file.size > maxFileSize) {
                this.toastShow(400, this.$t("toast.file_exceeds_size_limit"));
                return;
            }

            // Check if it's a YAML file
            if (file.type === "application/x-yaml" && file.name.endsWith(".yaml")) {
                try {
                    // Read file with 300 line limit
                    const limitedContent = await readFileWithLineLimit(file, 300);
                    // Convert YAML to JSON
                    const jsonReportData = parse(limitedContent);
                    // Save filename to store
                    this.$store.data.dataFilename = file.name;
                    // Save JSON report data to store
                    this.$store.data.dataJSON = jsonReportData;
                    // Save YAML report data to store
                    this.$store.data.dataYAML = limitedContent;
                    // Unlock magic button
                    this.$store.app.appMagicButtonIsLocked = false;
                    // Notify success
                    this.toastShow(200, this.$t("toast.success"));
                } catch (error) {
                    // Check if it's a line limit error
                    if (error.message.includes('exceeds_size_limit')) {
                        this.toastShow(400, this.$t("toast.file_exceeds_size_limit"));
                    } else {
                        this.toastShow(400, this.$t("toast.file_load_failure"));
                    }
                }
            } else {
                this.toastShow(400, this.$t("toast.file_invalid_type"));
            }
        } catch (error) {
            this.toastShow(400, this.$t("toast.file_load_failure"));
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
            this.$store.data.dataYAML = detail;
        }
    },

    dropzoneDownloadLink: {
        
        ["@click.prevent"]() {
            // Then trigger download via a fake link
            this.$nextTick(() => {
                const link = document.createElement("a");
                link.href = `data:application/x-yaml;base64,${btoa(this.$store.data.dataYAML)}`;
                link.download = this.$store.data.dataJSON?.group
                    ? `group_file_g${this.$store.data.dataJSON.group}.yaml`
                    : 'group_file_g1.yaml';
                link.click();
            });
        }
    },

    dropzoneResetLink: {
        ["@click.prevent"]() {
            // Cancel report data
            this.$store.data.dataFilename = "";
            this.$store.data.dataYAML = "";
            this.$store.data.dataJSON = {};
            // Lock magic button
            this.$store.app.appMagicButtonIsLocked = true;
        }
    },

    magicButton: {

        label: "next",

        async ["action"]() {
            try {
                // Save parse yaml data into store
                this.$store.data.dataJSON = parse(this.$store.data.dataYAML);
                // Reset api response
                this.$store.api.apiResponse = {};
                // Save api Request
                this.$store.api.apiRequest = {
                    endpoint: "api/report",
                    method: "POST",
                    queryParams: { "language": "it", with_sociogram: this.dropzoneWithSociogram },
                    bodyData: JSON.parse(JSON.stringify(this.$store.data.dataJSON))
                };
                // Save response to store
                this.$store.api.apiResponse = await this.apiHandleRequest(this.$store.api.apiRequest);
            } catch (error) {
                if ("name" in error && error.name == "YAMLParseError") {
                    // Save YAML error to store
                    this.$store.data.dataYAMLError = error;
                }
            } finally {
                // Go to notify
                this.navigationGoTo("notify");
            }
        }
    }
});
