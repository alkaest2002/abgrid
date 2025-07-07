export default () => ({

    init() {
        // Set initial value of newGroupFile
        this.newGroupFile = this.$store.abgrid.groupDataIsDirty;

        // Watch for changes in groupDataIsDirty
        this.$watch("$store.abgrid.groupDataIsDirty", 
            (isDirty) => {
                this.$store.abgrid.magicButtonIsLocked = 
                isDirty && !this.$store.abgrid.groupDataIsComplete
            }
        );
        
        // Watch for changes in newGroupFile
        this.$watch("newGroupFile", (newGroupFile) => {
            this.$store.abgrid.magicButtonIsLocked = 
                newGroupFile && !this.$store.abgrid.groupDataIsComplete;
        });
    },

    destroy() {
        // On destroy, unlock magic button
        this.$store.abgrid.magicButtonIsLocked = false;
    },

    newGroupFile: false,

    magicButton: {

        label: "next",

        async ["action"]() {
            // If no newGroupFile
            if (!this.newGroupFile) {
                // Reset groupData
                this.$store.abgrid.resetGroupData();
                // Fo to dropzone
                return this.navigationGoTo("group.dropzone")
                };
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
                // unlock magic button
                this.$store.abgrid.magicButtonIsLocked = true;
                // Go to notify
                this.navigationGoTo("notify");
            }
        }
    }
});
