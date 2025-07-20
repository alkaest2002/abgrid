export default () => ({

    initApi() {
        // Initialize request queue
        this.apiRequestQueue = [];
        this.apiIsProcessingQueue = false;
    },

    get apiBase() {
        return import.meta.env.DEV
            ? "http://localhost:7895"
            : "https://abgrid.onrender.com";
    },

    async apiPokeServer() {
        const apiResponse = await this.apiHandleRequest({
            endpoint: "",
            method: "GET"
        });
        this.$store.api.apiServerIsReachable = apiResponse?.statusCode === 200 || false;
    },

    async apiHandleRequest(request) {
        
        // If a request is already pending, queue this one
        if (this.$store.api.apiRequestIsPending) {
            return new Promise((resolve) => {
                this.apiRequestQueue.push({ request, resolve });
            });
        }

        // Process the request immediately
        return this.apiProcessRequest(request);
    },

    async apiProcessRequest(request) {
        try {
            // Save api request to store
            this.$store.api.apiRequest = request;
            // Reset api response
            this.$store.api.apiResponse = {};
            // Switch on api request pending flag
            this.$store.api.apiRequestIsPending = true;
            // Make api request to server and save response to store
            this.$store.api.apiResponse = await this.apiFetch(request);
            // retur responde
            return this.$store.api.apiResponse;
        // On error
        } catch (error) {
            // Save error to store
            this.$store.api.apiResponse = this.apiCreateResponse(500, "internal_error");
            return this.$store.api.apiResponse;
        } finally {
            // Switch off api request pending flag
            this.$store.api.apiRequestIsPending = false;
            // Destructure api request
            const { endpoint = "" } = this.$store.api.apiRequest;
            // Destructure api response
            const { statusCode: toastStatus = 400 } = this.$store.api.apiResponse;
            // Tostify specific endpoints only
            if (["api/report", "api/group"].includes(endpoint)) {
                toastStatus == 200
                    ? this.toastShowSuccess()
                    : this.toastShowError();
            }
            // Process next request in queue
            this.apiProcessNextInQueue();
        }
    },

    async apiProcessNextInQueue() {
        // Prevent concurrent queue processing
        if (this.apiIsProcessingQueue || this.apiRequestQueue.length === 0) {
            return;
        }

        // Switch on apiIsProcessingQueue flag
        this.apiIsProcessingQueue = true;
        
        try {
            // Get next request from queue
            const { request, resolve } = this.apiRequestQueue.shift();
            // Process the request
            const response = await this.apiProcessRequest(request);
            // Resolve the promise for the queued request
            resolve(response);
        } finally {
            // Switch off apiIsProcessingQueue flag 
            this.apiIsProcessingQueue = false;
        }
    },

    async apiFetch(config) {
        const {
            endpoint,
            method = "GET",
            headers = {},
            queryParams = {},
            bodyData = null,
            timeout = 45_000,
            ...otherOptions
        } = config;

        // 1 ENDPOINT VALIDATION (no full URLs allowed)
        if (typeof endpoint !== "string" || endpoint.includes("://")) {
            // return error
            return this.apiCreateResponse(400, "invalid_endpoint");
        }

        // 2 BUILD & VALIDATE URL
        const url = this.apiBuildUrl(`${this.apiBase}/${endpoint}`, queryParams);
        if (!import.meta.env.DEV && !url.startsWith("https://")) {
            // return error
            return this.apiCreateResponse(400, "insecure_url_in_production");
        }

        // 3 AUTH HEADER (server still must re‑check)
        if (this.$store.api.apiToken && endpoint !== "token") {
            headers.Authorization = `Bearer ${this.$store.api.apiToken}`;
        }

        // 4 ABORT + TIMEOUT
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            // 5 FETCH OPTIONS
            const fetchOptions = {
                method,
                headers: {
                    Accept: "application/json",
                    ...headers,
                },
                credentials: "same-origin",
                signal: controller.signal,
                ...otherOptions,
            };

            // 6 BODY VALIDATION (only plain JSON objects/arrays)
            if (method !== "GET" && bodyData != null) {
                if (
                    typeof bodyData !== "object" ||
                    bodyData instanceof FormData ||
                    bodyData instanceof Blob ||
                    bodyData instanceof ArrayBuffer ||
                    bodyData instanceof URLSearchParams
                ) {
                    // return error
                    return this.apiCreateResponse(400, "only_json_body_data_accepted");
                }
                try {
                    fetchOptions.headers["Content-Type"] = "application/json";
                    fetchOptions.body = JSON.stringify(bodyData);
                } catch {
                    // return error
                    return this.apiCreateResponse(400, "invalid_json_body_data");
                }
            }

            // 7 ACTUAL REQUEST
            const response = await fetch(url, fetchOptions);
            
            // 8 PARSE JSON (assume server returns JSON)
            try {
                // Get reponse as json data
                const jsonResponse = await response.json();

                // Create message
                const message = response.ok
                    ? "success"
                    : jsonResponse?.detail || `http_${response.status}_${response.statusText
                        .toLowerCase()
                        .replace(/[^a-z0-9]+/g, "_")}`;
                        // return api response
                        return this.apiCreateResponse(response.status, message, jsonResponse);
            } catch {
                // return error
                return this.apiCreateResponse(500, "malformed_json_from_server");
            }
            
        } catch (err) {
            const msg = err.name === "AbortError" 
                ? "request_timeout" 
                : "down";
            // return error
            return this.apiCreateResponse(500, msg);
        
        } finally {
            // Clear timer
            clearTimeout(timeoutId);
        }
    },


    apiCreateResponse(statusCode, message, data = { detail: message }) {
        return { statusCode, data };
    },

    apiBuildUrl(url, params) {
        if (!params || Object.keys(params).length === 0) return url;
        const u = new URL(url);
        Object.entries(params).forEach(([k, v]) => {
            if (v != null) u.searchParams.append(String(k), String(v));
        });
        return u.toString();
    },
});
