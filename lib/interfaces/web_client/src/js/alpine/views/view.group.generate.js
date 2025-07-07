export default () => ({

    resetButton: {

        [":class"]() { 
            return !this.$store.abgrid.groupDataIsComplete
                ? "opacity-50 cursor-not-allowed"
                : ""
        },

        ["@click.prevent"]() {
            this.$store.abgrid.resetGroupData();
        }
    },

    generateGroupButton: {

        [":class"]() { 
            return !this.$store.abgrid.groupDataIsComplete
                ? "opacity-50 cursor-not-allowed"
                : ""
        },
        
        async ["@click.prevent"]() {
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
