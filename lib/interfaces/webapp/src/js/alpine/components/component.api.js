/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
export default () => ({

    initApi() {},

    get apiBase() {
        return import.meta.env.DEV
            ? "http://localhost:7895"
            : import.meta.env.VITE_API_URL;
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
            compressionThreshold = 8 * 1024, // characters threshold before compressing
            ...otherOptions
        } = config;

        // 1 ENDPOINT VALIDATION (no full URLs allowed)
        if (typeof endpoint !== "string" || endpoint.includes("://")) {
            return this.apiCreateResponse(400, "invalid_endpoint");
        }

        // 2 BUILD & VALIDATE URL
        const url = this.apiBuildUrl(`${this.apiBase}/${endpoint}`, queryParams);
        if (!import.meta.env.DEV && !url.startsWith("https://")) {
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
                    "Accept-Encoding": "gzip, deflate, br",
                    ...headers,
                },
                credentials: "same-origin",
                signal: controller.signal,
                ...otherOptions,
            };

            // 6 BODY VALIDATION + OPTIONAL COMPRESSION (only plain JSON objects/arrays)
            if (method !== "GET" && bodyData != null) {
                const isPlainObjectOrArray =
                    typeof bodyData === "object" &&
                    bodyData != null &&
                    !(bodyData instanceof FormData) &&
                    !(bodyData instanceof Blob) &&
                    !(bodyData instanceof ArrayBuffer) &&
                    !(bodyData instanceof URLSearchParams);

                if (!isPlainObjectOrArray) {
                    return this.apiCreateResponse(400, "only_json_body_data_accepted");
                }

                // Serialize JSON
                let jsonBody;
                try {
                    jsonBody = JSON.stringify(bodyData);
                } catch {
                    return this.apiCreateResponse(400, "invalid_json_body_data");
                }

                // Default content type
                fetchOptions.headers["Content-Type"] = "application/json; charset=utf-8";
                
                // Try to compress
                const compressedBlob = await this.apiCompressJson(jsonBody);

                // If compression was successful
                if (compressedBlob) {
                    fetchOptions.body = compressedBlob;
                    fetchOptions.headers["Content-Encoding"] = "gzip";
                    fetchOptions.headers["Content-Length"] = String(compressedBlob.size);
                // Fallback to uncompressed
                } else {
                    fetchOptions.body = jsonBody;
                    fetchOptions.headers["Content-Length"] = String(new Blob([jsonBody]).size);
                }
            }

            // 7 ACTUAL REQUEST
            const response = await fetch(url, fetchOptions);

            // 8 PARSE JSON (AB-Grid server always returns JSON)
            try {
                const jsonResponse = await response.json();
                return this.apiCreateResponse(response.status, "success", jsonResponse);
            } catch {
                return this.apiCreateResponse(500, "malformed_json_from_server");
            }

        } catch (err) {
            const msg = err && err.name === "AbortError"
                ? "request_timeout"
                : "down";
            return this.apiCreateResponse(500, msg);

        } finally {
            clearTimeout(timeoutId);
        }
    },

    // Compress a JSON string with CompressionStream if available.
    // Returns a Blob containing compressed bytes or null if unsupported/fails.
    async apiCompressJson(jsonString) {
        try {
            if (typeof CompressionStream === "undefined") return null;
            const cs = new CompressionStream("gzip");
            const stream = new Blob([jsonString]).stream().pipeThrough(cs);
            const compressedBlob = await new Response(stream).blob();
            return compressedBlob;
        } catch {
            return null;
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