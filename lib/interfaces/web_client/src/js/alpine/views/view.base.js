export default () => ({
    
    async init() {

        // Update logout flow
        this.$store.abgrid.isLogoutFlowRunning = false;
        
        // Complete auth0 flow
        if (location.search.includes("state=") 
            && (location.search.includes("code=") || location.search.includes("error="))
        ) {
            // Handle redirect
            await window.Auth0Client.handleRedirectCallback();
            // Cleanup location
            window.history.replaceState({}, document.title, "/");
            // Update isAuthFlowRunning
            this.$store.abgrid.isLoginFlowRunning = false;
        }
        
        // Check authentication status
        const isAuthenticated = await window.Auth0Client.isAuthenticated();
        
        // if user is authenticated
        if (isAuthenticated) {
            // Save authentication status to store
            this.$store.abgrid.isAuthenticated = isAuthenticated;
            
            // Try to get the access token (JWT)
            try {
                // Get the access token (JWT)
                const accessToken = await window.Auth0Client.getTokenSilently();
                // Save the access token (JWT) to store
                this.$store.abgrid.token = accessToken
                // Notify success
                console.log("Auth0 tokem was stored")
            } catch (error) {
                // Notify error
                console.error("Error getting token:", error);
            }
        }
    },

    authButton: {
       
        "x-text"() {
            return this.$store.abgrid.isAuthenticated ? "logout" : "login"
        },

        "@click"() { 
            if (this.$store.abgrid.isAuthenticated) {
                // Start logout flow
                this.$store.abgrid.isLogoutFlowRunning = true;
                // Logout
                window.Auth0Client.logout(); 
                // Save authenticaton status to store
                this.$store.abgrid.isAuthenticated = false;
            } else {
                // Start login flow
                this.$store.abgrid.isLoginFlowRunning = true;
                // Login
                window.Auth0Client.loginWithRedirect();
            }
        },
    }
});
