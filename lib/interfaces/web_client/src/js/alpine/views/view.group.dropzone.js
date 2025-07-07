export default () => ({

    fileWasDropped: false,

    filename: null,

    dropzone: {
        ["@dragover.prevent"]() {
           
        },
        ["@drop.prevent"]($event) {
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
                        this.$store.abgrid.yaml = evt.target.result;
                    };
                    reader.readAsText(file);
                }
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
