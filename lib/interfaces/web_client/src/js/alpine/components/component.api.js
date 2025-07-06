export default () => ({

    initApi() {
        console.log("initApi");
    },

    get apiBase() {
        return import.meta.env.DEV
            ? "http://localhost:7895"
            : "https://abgrid.onrender.com"
    },

    apiGetEndpoint(endpoint) {
        return `${this.apiBase}/${endpoint}`;
    },

    async apiHandleRequest(request) {
        if (!request || Object.keys(request).length === 0) return;

        try {
            // Set loading state
            this.$store.abgrid.appIsRunning = true;
            this.$store.abgrid.appResponse = {};

            const response = await this.apiFetch(request);

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

    async apiFetch(config) {
        // Extract endpoint and use remaining keys for fetch configuration
        const { endpoint, ...fetchConfig } = config;

        if (!endpoint) {
            throw new Error('Endpoint is required');
        }

        // Set defaults for fetch configuration
        const {
            method = 'GET',
            headers = {},
            queryParams = {},
            bodyData = null,
            timeout = 30000,
            ...otherOptions
        } = fetchConfig;

        // Build URL
        const url = this.apiBuildUrl(this.apiGetEndpoint(endpoint), queryParams);
        
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
                signal: controller.signal,
                ...otherOptions // Spread any additional fetch options
            };

            // Add body for non-GET requests
            if (method !== 'GET' && bodyData) {
                fetchOptions.body = JSON.stringify(bodyData);
            }
            const response = await fetch(url, fetchOptions);

            clearTimeout(timeoutId);

            // Parse response data based on content type
            const contentType = response.headers.get('Content-Type') || '';
            let responseData;
            
            if (contentType.includes('application/json')) {
                responseData = await response.json();
            } else if (contentType.includes('text/html')) {
                responseData = await response.text();
            } else if (contentType.includes('text/yaml') || contentType.includes('text/plain')) {
                responseData = await response.text();
            } else {
                responseData = await response.text();
            }

            // Always return an object with status code and data
            const result = {
                status: response.status,
                statusText: response.statusText,
                ok: response.ok,
                data: responseData,
                headers: Object.fromEntries(response.headers.entries())
            };

            // If response is not ok, include error information but don't throw
            if (!response.ok) {
                result.error = true;
                result.message = `HTTP ${response.status}: ${response.statusText}`;
                
                // Try to extract error details from response data
                if (responseData && typeof responseData === 'object' && responseData.detail) {
                    result.message = responseData.detail;
                }
            }

            return result;

        } catch (error) {
            clearTimeout(timeoutId);
            
            // For network errors, timeouts, etc., return consistent structure
            const result = {
                status: 0, // 0 indicates network error
                statusText: 'Network Error',
                ok: false,
                error: true,
                message: error.name === 'AbortError' ? 'Request timeout' : error.message,
                data: null,
                headers: {}
            };
            
            return result;
        }
    },

    apiBuildUrl(url, params) {
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
