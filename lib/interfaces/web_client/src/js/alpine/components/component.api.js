export default () => ({
    
    initApi() {
        console.log("initApi");
        this.$watch("$store.abgrid.apiRequest", (request) => this.handleApiRequest(request));
    },

    async handleApiRequest(request) {
        if (!request || Object.keys(request).length === 0) return;
        
        console.log("API Request:", request);
        
        try {
            // Set loading state
            this.$store.abgrid.appIsRunning = true;
            this.$store.abgrid.appResponse = {};
            
            const response = await this.fetchApi(request);
            
            // Store successful response
            this.$store.abgrid.apiResponse = response;
            
        } catch (error) {
            // Store error in appResponse
            this.$store.abgrid.appResponse = {
                error: true,
                message: error.message,
                timestamp: new Date().toISOString()
            };
            
        } finally {
            // Always reset loading state
            this.$store.abgrid.appIsRunning = false;
        }
    },

    async fetchApi(config) {
        const {
            endpoint,
            method = 'GET',
            headers = {},
            queryParams = {},
            bodyData = null,
            timeout = 30000
        } = config;

        // Build URL using store's apiEndpoint method
        const url = this.buildUrl(this.$store.abgrid.apiEndpoint(endpoint), queryParams);
        
        // Prepare headers with defaults
        const finalHeaders = {
            ...headers
        };

        // Add auth header if token exists (required for all endpoints except /token)
        if (this.$store.abgrid.apiToken && endpoint !== 'token') {
            finalHeaders.Authorization = `Bearer ${this.$store.abgrid.apiToken}`;
        }

        // Set Content-Type for POST requests with JSON body
        if (method !== 'GET' && bodyData) {
            finalHeaders['Content-Type'] = 'application/json';
        }

        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const fetchOptions = {
                method,
                headers: finalHeaders,
                signal: controller.signal
            };

            // Add body for non-GET requests
            if (method !== 'GET' && bodyData) {
                fetchOptions.body = JSON.stringify(bodyData);
            }

            const response = await fetch(url, fetchOptions);

            clearTimeout(timeoutId);

            if (!response.ok) {
                // Try to get error details from response
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    if (errorData.detail) {
                        errorMessage = errorData.detail;
                    }
                } catch (e) {
                    // If can't parse JSON, use default error message
                }
                throw new Error(errorMessage);
            }

            // Parse response based on content type
            const contentType = response.headers.get('Content-Type') || '';
            
            if (contentType.includes('application/json')) {
                return await response.json();
            } else if (contentType.includes('text/html')) {
                return await response.text();
            } else if (contentType.includes('text/yaml') || contentType.includes('text/plain')) {
                return await response.text();
            } else {
                return response;
            }

        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            
            throw error;
        }
    },

    buildUrl(url, params) {
        if (!params || Object.keys(params).length === 0) {
            return url;
        }

        const urlObj = new URL(url);
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                urlObj.searchParams.append(key, value);
            }
        });

        return urlObj.toString();
    }
})