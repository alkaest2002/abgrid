export default () => ({

    magicButton: {

        label: "next",

        async ["action"]() {
            // 11 hours and 45 minutes in milliseconds
            const expirationTimeInMs = 11 * 60 * 60 * 1000 + 45 * 60 * 1000; 
            const currentTime = Date.now();
            const tokenTimestamp = this.$store.abgrid.apiTokenTimestamp;

            // Request jwt token if not in store or if the token is expired
            if (!this.$store.abgrid.apiToken || (currentTime - tokenTimestamp > expirationTimeInMs)) {
                
                // Save api request to store
                this.$store.abgrid.apiRequest = {
                    endpoint: "api/token",
                    method: "GET",
                };
                
                // Call server
                this.$store.abgrid.apiResponse = await this.apiHandleRequest(this.$store.abgrid.apiRequest);
                
                // Save token in store
                this.$store.abgrid.apiToken = this.$store.abgrid.apiResponse.data.detail;
                this.$store.abgrid.apiTokenTimestamp = currentTime;
            }
            
            // Navigate to generate
            this.navigationGoTo("generate");
        }
    }
});
