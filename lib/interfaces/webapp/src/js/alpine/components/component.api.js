/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
export default () => ({

    initApi() {},

    get apiBase() {
        return import.meta.env.DEV
            ? "http://localhost:7895"
            : "https://abgrid.onrender.com";
    },

    async apiPokeServer() {
        // Poke server
        const { statusCode } = await this.apiProcessRequest({ endpoint: "", method: "GET"});
        // Save server reachability to store
        this.$store.api.apiServerIsReachable = statusCode === 200;
    },

    async apiProcessRequest(request) {
        try {
            // Switch on api request pending flag
            this.$store.api.apiRequestIsPending = true;
            // Save api request to store
            this.$store.api.apiRequest = request;
            // Reset api response
            this.$store.api.apiResponse = {};
            // Make api request to server
            const response = await this.apiFetch(request);
            // Save api response to store
            this.$store.api.apiResponse = response;
        } catch (error) {
            // Save error to store
            this.$store.api.apiResponse = this.apiCreateResponse(500, "internal_error");
        } finally {
            // Switch off api request pending flag
            this.$store.api.apiRequestIsPending = false;
            // Return apiResponse
            return this.$store.api.apiResponse;
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

        // 3 AUTH HEADER
        if (this.$store.api.apiToken) {
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
                    typeof bodyData !== "object" 
                        || bodyData instanceof FormData 
                        || bodyData instanceof Blob 
                        || bodyData instanceof ArrayBuffer 
                        || bodyData instanceof URLSearchParams
                ) {
                    return this.apiCreateResponse(400, "only_json_body_data_accepted");
                }
                try {
                    fetchOptions.headers["Content-Type"] = "application/json";
                    const jsonBody = JSON.stringify(bodyData);
                    fetchOptions.body = jsonBody;
                    fetchOptions.headers["Content-Length"] = new Blob([jsonBody]).size.toString();
                } catch {
                    return this.apiCreateResponse(400, "invalid_json_body_data");
                }
            }

            // 7 ACTUAL REQUEST
            const response = await fetch(url, fetchOptions);
            
            // 8 PARSE JSON (AB-Grid server alwyas returns JSON)
            try {
                // Get response as json data
                const jsonResponse = await response.json();
                return this.apiCreateResponse(response.status, "success", jsonResponse);
            } catch {
                return this.apiCreateResponse(500, "malformed_json_from_server");
            }
            
        } catch (err) {
            const msg = err.name === "AbortError" 
                ? "request_timeout" 
                : "down";
            return this.apiCreateResponse(500, msg);
        
        } finally {
            // Clear timer
            clearTimeout(timeoutId);
        }
    },

    apiCreateResponse(statusCode, statusMessage, data = { detail: statusMessage }) {
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
