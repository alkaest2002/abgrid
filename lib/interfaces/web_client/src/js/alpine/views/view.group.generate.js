export default () => ({

    init() {
        this.$watch("$store.abgrid.groupData", () => {
            this.$store.abgrid.appIsLocked = 
                this.$store.abgrid.groupDataIsDirty && !this.$store.abgrid.groupDataIsComplete
        });
    },

    resetButton: {

        [":class"]() { 
            return !this.$store.abgrid.groupDataIsComplete && !this.$store.abgrid.groupDataIsDirty
                ? "opacity-50 cursor-not-allowed"
                : "cursor-pointer"
        },

        ["@click.prevent"]() {
            this.$store.abgrid.resetGroupData();
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
