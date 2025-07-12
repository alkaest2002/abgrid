export default () => ({

    initApi() {

    },

    get apiBase() {
        return import.meta.env.DEV
            ? "http://localhost:7895"
            : "https://abgrid.onrender.com"
    },

    async apiHandleRequest(request) {
        let apiResponse;
        try {
            // Fetch and save response to store
            apiResponse = await this.apiFetch(request);
        } catch (error) {
            // Save error to store
            apiResponse = this.createResponse(500, error.message);
        } finally {
            return apiResponse;
        }
    },

    async apiFetch(config) {
        // Destructure onject
        const { 
            endpoint, 
            method = 'GET', 
            headers = {}, 
            queryParams = {}, 
            bodyData = null, 
            timeout = 30000, 
            ...otherOptions 
        } = config;

        // Build URL and headers
        const url = this.apiBuildUrl(`${this.apiBase}/${endpoint}`, queryParams);

        // Add auth header (except for token endpoint)
        if (this.$store.abgrid.apiToken && endpoint !== "token") {
            headers.Authorization = `Bearer ${this.$store.abgrid.apiToken}`;
        }

        // Init abort controller
        const { signal, abort } = new AbortController();
        
        // Setup abort fetch on timeout
        const timeoutId = setTimeout(() => abort(), timeout);

        try {
            // Init fetch options
            const fetchOptions = {
                method,
                headers,
                signal,
                ...otherOptions
            };

            // Add Content-Type and body handling - ONLY JSON allowed
            if (method !== "GET" && bodyData) {
                // Check if bodyData is not a plain object/array (reject FormData, Blob, etc.)
                if (bodyData instanceof FormData || 
                    bodyData instanceof Blob || 
                    bodyData instanceof ArrayBuffer ||
                    bodyData instanceof URLSearchParams ||
                    typeof bodyData === 'string') {
                    
                    return this.createResponse(400, "Only JSON body data is accepted");
                }

                // Only accept plain objects/arrays that can be JSON stringified
                try {
                    headers["Content-Type"] = "application/json";
                    fetchOptions.body = JSON.stringify(bodyData);
                } catch (jsonError) {
                    return this.createResponse(400, "Invalid JSON body data");
                }
            }

            // Call the api
            const response = await fetch(url, fetchOptions);

            // Parse response data - assume server always returns JSON
            const data = await response.json();

            // Extract message from response
            const message = response.ok
                ? "success"
                : (data?.detail || `HTTP ${response.status}: ${response.statusText}`);

            return this.createResponse(response.status, message, data);

        } catch (error) {
            const message = error.name === "AbortError" ? "Request timeout" : error.message;
            return this.createResponse(500, message);

        } finally {
            clearTimeout(timeoutId);
        }
    },

    createResponse(statusCode, message, data = { detail: "unknown_error" }) {
        return {
            statusCode,
            message,
            data
        };
    },

    apiBuildUrl(url, params) {
        // Jusr return url if there are no params
        if (!params || Object.keys(params).length === 0) return url;

        // Create new URL
        const urlObj = new URL(url);

        // Add params
        Object.entries(params).forEach(([key, value]) => {
            if (value != null) {
                urlObj.searchParams.append(key, value);
            }
        });
        
        return urlObj.toString();
    }
})
