import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
    ["appIsOnline", true],
    ["appIsLocked", false],
    ["appIsRunning", false],
    ["appLanguage", "it"],
    ["appResponse", {}],
    ["apiToken", ""],
    ["apiRequest", {}],
    ["apiResponse", {}],
    ["groupData", {
        "project_title": "",
        "question_a": "",
        "question_b": "",
        "group": null,
        "members": null
    }]
];

const abgridStore = (Alpine) => ({
    ...initState(stateFn, Alpine, "_app"),

    wipeState(omit = []) {
        wipeState.call(this, stateFn, omit);
    },
});

export { abgridStore };
