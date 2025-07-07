export default () => ({

    init() {
        // Lock magic button on these conditions
        this.$store.abgrid.magicButtonIsLocked = 
            this.$store.abgrid.groupDataIsComplete || this.$store.abgrid.groupDataIsDirty;
        
        // Watch for changes in group data 
        this.$watch("$store.abgrid.groupData", 
            () => {
                switch(true) {
                    case this.$store.abgrid.groupDataIsComplete && !this.fileWasDownloaded:
                        this.$store.abgrid.magicButtonIsLocked = true;
                        break;
                    case !this.$store.abgrid.groupDataIsComplete && this.$store.abgrid.groupDataIsDirty:
                        this.$store.abgrid.magicButtonIsLocked = true;
                        break;
                } 
            }
        )
    },

    destroy() {
        // On destroy, unlock magic button
        this.$store.abgrid.magicButtonIsLocked = false;
    },

    fileWasDownloaded: false,

    resetButton: {

        [":class"]() { 
            return !this.$store.abgrid.groupDataIsComplete && !this.$store.abgrid.groupDataIsDirty
                ? "opacity-50 cursor-not-allowed"
                : "cursor-pointer"
        },

        ["@click.prevent"]() {
            this.$store.abgrid.resetGroupData();
            this.$store.abgrid.magicButtonIsLocked = false;
        }
    },

    generateGroupButton: {

        [":class"]() { 
            return !this.$store.abgrid.groupDataIsComplete
                ? "opacity-50 cursor-not-allowed"
                : "cursor-pointer"
        },
        
        async ["@click.prevent"]() {
            // Make sure form data is complete
            if (!this.$store.abgrid.groupDataIsComplete)
                return;
            // Store api request 
            this.$store.abgrid.apiRequest = {
                endpoint: "api/group",
                method: "POST",
                queryParams: {"language": "it"},
                bodyData: JSON.parse(JSON.stringify(this.$store.abgrid.groupData))
            };
            // Call server
            await this.apiHandleRequest(this.$store.abgrid.apiRequest);
            // On api error
            if (this.$store.abgrid.apiResponse.statusCode >= 400) {
                // unlock ui
                this.fileWasDownloaded = true;
                // Go to notify
                this.navigationGoTo("notify");
            }
        }
    },

    magicButton: {

        label: "next",

        ["action"]() {
            this.navigationGoTo("group.dropzone");
        }
    }
});
