import { parse } from "yaml";
import  { readFileWithLineLimit } from "../usables/use.text.reader";

export default () => ({

    init() {
        // Update magic button locked status
        this.$nextTick(() => {
            this.$store.app.appMagicButtonIsLocked = 
               Object.keys(this.$store.data?.dataJSON || []).length == 0;
        });
    },

    dropzoneWithSociogram: true,

    async dropzoneProcessFile(file) {
        try {
            
            // Check file size first (100KB = 100 * 1024 bytes)
            const maxFileSize = 100 * 1024;
            if (file.size > maxFileSize) {
                this.toastShowError("file_exceeds_size_limit");
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
                    // Toast success
                    this.toastShowSuccess();
                // On load failure
                } catch (error) {
                    // Toast error
                    this.toastShowError("file_load_failure");
                }
            // On invalid file type
            } else {
                // Toast error
                this.toastShowError("file_invalid_type");
            }
        // On error
        } catch (error) {
            // Toast error
            this.toastShowError("file_load_failure");
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
            // Wipe data
            this.$store.data.wipeState();
            // Lock magic button
            this.$store.app.appMagicButtonIsLocked = true;
        }
    },

    magicButton: {

        label: "next",

        async ["action"]() {
            try {
                // Update JSON data in store
                this.$store.data.dataJSON = parse(this.$store.data.dataYAML);
                
                // Create api request
                const apiRequest = {
                    endpoint: "api/report",
                    method: "POST",
                    queryParams: { "language": "it", with_sociogram: this.dropzoneWithSociogram },
                    bodyData: JSON.parse(JSON.stringify(this.$store.data.dataJSON))
                };
                
                // Make api request to server
                await this.apiHandleRequest(apiRequest);
                
            // On error
            } catch (error) {
                if ("name" in error && error.name == "YAMLParseError") {
                    // Save YAML error to store
                    this.$store.data.dataYAMLError = error;
                    
                    // Toast error
                    this.toastShowError("file_invalid_yaml");
                }
            } finally {
                // Go to notify
                this.navigationGoTo("notify");
            }
        }
    }
});
