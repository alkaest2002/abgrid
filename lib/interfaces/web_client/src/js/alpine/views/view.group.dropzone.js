import YAML from "yaml";

export default () => ({

    fileWasDropped: false,

    filename: null,

    dropzone: {
        ["@dragover.prevent.stop"]() {
           
        },
        ["@drop.prevent.stop"]($event) {
            try {
                // Check if files were dropped
                if ($event.dataTransfer.files && $event.dataTransfer.files.length > 0) {
                    // Get file
                    const file = $event.dataTransfer.files[0];
                    // Store filename
                    this.filename = file.name;
                    // Check if it's a text file
                    if (file.type === "application/x-yaml" && file.name.endsWith('.yaml')) {
                        const reader = new FileReader();
                        reader.onload = (evt) => {
                            this.fileWasDropped = true;
                            this.$store.abgrid.yaml = YAML.parse(evt.target.result);
                            this.toastPush(200, this.$t("ops.successful_operation"));
                        };
                        reader.readAsText(file);
                    }
                }
            } catch (error) {
                this.toastPush(400, this.$t("errors.yaml_load_failure"));
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
