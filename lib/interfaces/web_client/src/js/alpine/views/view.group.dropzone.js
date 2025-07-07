import YAML from "yaml";

export default () => ({

    fileWasDropped: false,

    filename: null,

    // Abstracted common file processing logic
    processFile(file) {
        try {
            // Store filename
            this.filename = file.name;
            
            // Check if it's a YAML file
            if (file.type === "application/x-yaml" && file.name.endsWith(".yaml")) {
                const reader = new FileReader();
                reader.onload = (evt) => {
                    this.fileWasDropped = true;
                    this.$store.abgrid.yaml = YAML.parse(evt.target.result);
                    this.toastPush(200, this.$t("ops.successful_operation"));
                };
                reader.readAsText(file);
            } else {
                this.toastPush(400, this.$t("errors.invalid_file_type"));
            }
        } catch (error) {
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
