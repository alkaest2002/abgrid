export default () => ({

    initApi() { },

    get apiBase() {
        return import.meta.env.DEV
            ? "http://localhost:7895"
            : "https://abgrid.onrender.com";
    },

    async apiHandleRequest(request) {
        try {
            return await this.apiFetch(request);
        } catch (error) {
            // unexpected JS error
            return this.createResponse(500, "internal_error");
        }
    },

    async apiFetch(config) {
        const {
            endpoint,
            method = "GET",
            headers = {},
            queryParams = {},
            bodyData = null,
            timeout = 30_000,
            ...otherOptions
        } = config;

        // 1 ENDPOINT VALIDATION (no full URLs allowed)
        if (typeof endpoint !== "string" || endpoint.includes("://")) {
            return this.createResponse(400, "invalid_endpoint");
        }

        // 2 BUILD & VALIDATE URL
        const url = this.apiBuildUrl(`${this.apiBase}/${endpoint}`, queryParams);
        if (!import.meta.env.DEV && !url.startsWith("https://")) {
            return this.createResponse(400, "insecure_url_in_production");
        }

        // 3 AUTH HEADER (server still must re‑check)
        if (this.$store.abgrid.apiToken && endpoint !== "token") {
            headers.Authorization = `Bearer ${this.$store.abgrid.apiToken}`;
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
                    return this.createResponse(400, "only_json_body_data_accepted");
                }
                try {
                    fetchOptions.headers["Content-Type"] = "application/json";
                    fetchOptions.body = JSON.stringify(bodyData);
                } catch {
                    return this.createResponse(400, "invalid_json_body_data");
                }
            }

            // 7 ACTUAL REQUEST
            const response = await fetch(url, fetchOptions);

            // 8 PARSE JSON (assume server returns JSON)
            let data;
            try {
                data = await response.json();
            } catch {
                return this.createResponse(500, "malformed_json_from_server");
            }

            // 9 FORMULATE RESPONSE
            const message = response.ok
                ? "success"
                : data?.detail || `http_${response.status}_${response.statusText
                    .toLowerCase()
                    .replace(/[^a-z0-9]+/g, "_")}`;

            return this.createResponse(response.status, message, data);

        } catch (err) {
            const msg =
                err.name === "AbortError" ? "request_timeout" : "network_error";
            return this.createResponse(500, msg);
        } finally {
            clearTimeout(timeoutId);
        }
    },

    createResponse(statusCode, message, data = { detail: "unknown_error" }) {
        return { statusCode, message, data };
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
