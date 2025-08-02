import  { readFileWithLineLimit } from "../usables/use.text.reader";

export default () => ({

    init() {
        // Lock magic button
        this.$nextTick(() => this.$store.app.appMagicButtonIsLocked = true);
    },

    dropzoneEmptyIsDragOver: false,

    async dropzoneEmptyProcessFile(file) {
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
                    // Save filename to store
                    this.$store.data.dataFilename = file.name;
                    // Save YAML report data to store
                    this.$store.data.dataYAML = limitedContent;
                    // Unlock magic button
                    this.$store.app.appMagicButtonIsLocked = false;
                    // Toast success
                    this.toastShowSuccess();
                    // Go to dropzone data
                    this.navigationGoTo("dropzone.data");
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

    dropzoneEmptyContainer: {
        [":class"]() {
            return this.dropzoneEmptyIsDragOver
                ? "border-2 border-dashed border-gray-300"
                : "border-2 border-dashed border-transparent"
        },

        ["@click"]() {
            // Cleanup function
            const cleanup = () => {
                document.body.contains(fileInput) && document.body.removeChild(fileInput);
            };

            // Create file input element
            const fileInput = document.createElement("input");
            fileInput.type = "file";
            fileInput.accept = ".yaml, application/x-yaml";
            fileInput.style.display = "none";
                        
            // Handle file selection
            fileInput.onchange = (event) => {
                if (event.target.files && event.target.files.length > 0) {
                    this.dropzoneEmptyProcessFile(event.target.files[0]);
                }
                cleanup();
            };
            
            // Handle cancel (when user closes dialog without selecting)
            fileInput.oncancel = cleanup;
            
            // Append to body, click, then clean up with delay
            document.body.appendChild(fileInput);
            fileInput.click();
            setTimeout(cleanup, 100);
        },

        ["@keydown.enter.window"]() {
            this.$el.click();
        },

        ["@keydown.space.prevent.window"]() {
            this.$el.click();
        },

        ["@dragover.prevent.stop"]() {
            this.dropzoneEmptyIsDragOver = true;
        },

        ["@dragleave.prevent.stop"]() {
            this.dropzoneEmptyIsDragOver = false;
        },

        ["@drop.prevent.stop"]($event) {
            this.dropzoneEmptyIsDragOver = false;
            // Check if files were dropped
            if ($event.dataTransfer.files && $event.dataTransfer.files.length > 0) {
                this.dropzoneEmptyProcessFile($event.dataTransfer.files[0]);
            }
        }
    },

    magicButton: {

        label: "next",

        async ["action"]() {
           this.navigationGoTo("dropzone.data");
        }
    }
});
