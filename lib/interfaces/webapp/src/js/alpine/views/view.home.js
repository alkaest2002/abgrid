export default () => ({

    async init() {

        // Save api request to store
        this.$store.abgrid.apiRequest = {
            endpoint: "",
            method: "GET",
        };
        
        // Call server
        this.$store.abgrid.apiResponse = await this.apiHandleRequest(this.$store.abgrid.apiRequest);
    },

    get serverStatus() {
        return this.$store.abgrid.apiResponse?.statusCode == 200
            ? `<span>&#128994;</span> <span class='italic'>${this.$store.abgrid.apiResponse.data.detail}</span>`
            : "<span>&#128308;</span> <span class='italic'>il server non risponde</span>"
    },

    getServerStatus: {
        ["x-html"]() {
            return this.serverStatus;
        }
    },

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
                
                // Save token and token timestamp in store
                this.$store.abgrid.apiToken = this.$store.abgrid.apiResponse.data.detail;
                this.$store.abgrid.apiTokenTimestamp = currentTime;
            }
            
            // Navigate to generate
            this.navigationGoTo("generate");
        }
    }
});
