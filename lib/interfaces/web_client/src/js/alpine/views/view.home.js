export default () => ({

    magicButton: {

        label: "next",

        async ["action"]() {
            // Request jwt token is not in store
            if (!this.$store.abgrid.apiToken) {
                // Save api request to store
                this.$store.abgrid.apiRequest = {
                    endpoint: "api/token",
                    method: "GET",
                };
                // Call server
                this.$store.abgrid.apiResponse = await this.apiHandleRequest(this.$store.abgrid.apiRequest);
                // Save token in store
                this.$store.abgrid.apiToken = this.$store.abgrid.apiResponse.data.detail;
            }
            // Navigate to generate
            this.navigationGoTo("generate");
        }
    }
});
