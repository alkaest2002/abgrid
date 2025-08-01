import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
    ["dataFilename", ""],
    ["dataYAML", ""],
    ["dataYAMLError", {}],
    ["dataGroup", {
        "project_title": "",
        "question_a": "",
        "question_b": "",
        "group": null,
        "members": null
    }]
];

const abgridDataStore = (Alpine) => ({
    
    ...initState(stateFn, Alpine, "_data"),

    get dataGroupIsDirty() {
        return Object
            .values(this.dataGroup)
            .filter(Boolean)
            .reduce((acc, itr) => acc + !!itr, 0) > 0
    },

    get dataGroupIsComplete() {
        return Object
            .values(this.dataGroup)
            .filter(Boolean)
            .reduce((acc, itr) => acc + !!itr, 0) == Object.keys(this.dataGroup).length
    },

    resetdDataGroup() {
        this.wipeState(["dataGroup"]);
    },

    wipeState(resetProps = []) {
        wipeState(this, stateFn, resetProps);
    },
});

export { abgridDataStore };
