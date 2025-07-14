export default () => ({

    async init() {

        // Create api request to probe server
        const apiRequest = {
            endpoint: "",
            method: "GET",
        };
        
        // Make api request to server
        await this.apiHandleRequest(apiRequest);
        
        // Get api response status code and message from server with defaults
        const { 
            statusCode = 400, 
            data: { detail: message = "server_down" }
        } = this.$store.api.apiResponse;

        // Save status code and message to local props
        this.serverIsAlive = statusCode == 200;
        this.serverIsAliveMessage = this.$t(`server.${message}`);
    },

    serverIsAlive: true,
    serverIsAliveMessage: "server_alive_and_kicking",

    get serverStatusMessage() {
        return this.serverIsAlive
            ? `<span>&#128994;</span> <span class='italic'>${this.serverIsAliveMessage}</span>`
            : `<span>&#128308;</span> <span class='italic'>${this.serverIsAliveMessage}</span>`
    },

    serverStatus: {
        ["x-html"]() {
            return this.serverStatusMessage;
        }
    },

    magicButton: {

        label: "next",

        async ["action"]() {
            // 11 hours and 45 minutes in milliseconds
            const expirationTimeInMs = 11 * 60 * 60 * 1000 + 45 * 60 * 1000; 
            const currentTime = Date.now();
            const tokenTimestamp = this.$store.api.apiTokenTimestamp;

            // Request jwt token if not in store or if the token is expired
            if (!this.$store.api.apiToken || (currentTime - tokenTimestamp > expirationTimeInMs)) {
                
                // Create api request
                const apiRequest = {
                    endpoint: "api/token",
                    method: "GET",
                };
                
                // Make api request to server
                await this.apiHandleRequest(apiRequest);
                
                // Save token and token timestamp to store
                this.$store.api.apiToken = this.$store.api.apiResponse.data.detail;
                this.$store.api.apiTokenTimestamp = currentTime;
            }
            
            // Navigate to generate
            this.navigationGoTo("generate");
        }
    }
});
