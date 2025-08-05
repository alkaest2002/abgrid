export function createEmptyApiRequest() {
    return {
        endpoint: "",
        method: "GET",
        headers: {},
        queryParams: {},
        bodyData: {},
        timeout: 45_000
        // Any additional properties will be spread into the request object
    };
};

export function createEmptyApiResponse() {
    return {
        statusCode: null,
        data: {
            detail: null
            // Any additional properties will be spread into the response object
        }
    };
};

export function createEmptyGroupData() {
    return {
        project_title: "",
        question_a: "",
        question_b: "",
        group: null,
        members: null
    };
};

export function createEmptyYamlParseError() {
    return {
        name: "",
        code: "",
        message: "",
        pos: [],
        linePos: []
    };
}