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

export function createEmptyMultiStepData() {
    return {
        step1: {},
        step2: {},
        step3: {},
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