export default () => ({

    async init() {

        // Poke server
        await this.apiPokeServer();

        // preload pages
        this.$store.app.appIsOnline && window.Taxi.preload(`/pages/${this.$store.app.appLanguage}.generate.html`);
        this.$store.app.appIsOnline && window.Taxi.preload(`/pages/${this.$store.app.appLanguage}.dropzone.html`);
        this.$store.app.appIsOnline && window.Taxi.preload(`/pages/${this.$store.app.appLanguage}.notify.html`);
    },

    serverIsAlive: true,
    serverIsAliveMessage: "up",

    get serverStatusMessage() {
        return this.$store.api.apiServerIsReachable
            ? `<span>&#128994;</span> <span class='italic'>${this.$t('server.up')}</span>`
            : `<span>&#128308;</span> <span class='italic'>${this.$t('server.down')}</span>`
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
