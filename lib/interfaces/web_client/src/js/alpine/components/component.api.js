export default () => ({

    initApi() {
        console.log("initApi");
    },

    get apiBase() {
        return import.meta.env.DEV
            ? "http://localhost:7895"
            : "https://abgrid.onrender.com"
    },

    async apiHandleRequest(request) {
        try {
            // Lock app
            this.$store.abgrid.appIsRunning = true;
            // Fetch and save response to store
            this.$store.abgrid.apiResponse = await this.apiFetch(request);
        } catch (error) {
            // Save error to store
            this.$store.abgrid.apiResponse = this.createResponse(500, error.message);
        } finally {
            // Unlock app
            this.$store.abgrid.appIsRunning = false;
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
        if (this.$store.abgrid.apiToken && endpoint !== 'token') {
            headers.Authorization = `Bearer ${this.$store.abgrid.apiToken}`;
        }

        // Add Content-Type for requests with body
        if (method !== 'GET' && bodyData) {
            headers['Content-Type'] = 'application/json';
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

            // Add Content-Type and body handling
            if (method !== 'GET' && bodyData) {
                if (bodyData instanceof FormData || bodyData instanceof Blob || bodyData instanceof ArrayBuffer) {
                    // Don't set Content-Type - let the browser set it automatically
                    // Don't stringify - use the data as-is
                    fetchOptions.body = bodyData;
                } else {
                    // For regular objects/arrays, stringify and set JSON content type
                    headers['Content-Type'] = 'application/json';
                    fetchOptions.body = JSON.stringify(bodyData);
                }
            }

            // Call the api
            const response = await fetch(url, fetchOptions);

            // Parse response data
            const contentType = response.headers.get('Content-Type') || '';
            const data = contentType.includes('application/json')
                ? await response.json()
                : await response.text();

            // Extract message from response
            const message = response.ok
                ? 'Success'
                : (data?.detail || `HTTP ${response.status}: ${response.statusText}`);

            return this.createResponse(response.status, message, data);

        } catch (error) {
            const message = error.name === 'AbortError' ? 'Request timeout' : error.message;
            return this.createResponse(500, message);

        } finally {
            clearTimeout(timeoutId);
        }
    },

    createResponse(statusCode, message, data = { detail: null }) {
        return {
            statusCode,
            message,
            data
        };
    },

    apiBuildUrl(url, params) {
        if (!params || Object.keys(params).length === 0) return url;

        const urlObj = new URL(url);
        Object.entries(params).forEach(([key, value]) => {
            if (value != null) {
                urlObj.searchParams.append(key, value);
            }
        });
        return urlObj.toString();
    }
})
