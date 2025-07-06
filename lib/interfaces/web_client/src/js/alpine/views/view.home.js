export default () => ({

    magicButton: {

        label: "next",

        async ["action"]() {
            // Handle metakey
            if (this.magicButtonMetaKeyIsPressed)
                return this.navigateTo("/");
            // Store api request 
            this.$store.abgrid.apiRequest = {
                endpoint: "api/token",
                method: "GET",
            };
            // Hit api
            await this.apiHandleRequest(this.$store.abgrid.apiRequest);
            // Store token
            this.$store.abgrid.apiToken = this.$store.abgrid.apiResponse.data.detail;
            // Navigate to group
            this.navigateTo("generate.group");
        }
    }
});
