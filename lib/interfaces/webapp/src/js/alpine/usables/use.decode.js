export function decodeBase64(base64EncodedData) {
    const binary = atob(base64EncodedData);
    const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));
    return new TextDecoder("utf-8").decode(bytes);
}

export function parseToJson(stringifiedData) {
    return JSON.parse(stringifiedData);
}

export function base64ToJson(base64EncodedData) {
    const jsonString = decodeBase64(base64EncodedData);
    return parseToJson(jsonString);
}