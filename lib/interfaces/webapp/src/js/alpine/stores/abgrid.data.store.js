import { initState, wipeState } from "../usables/use.alpine.store.js";

const stateFn = () => [
    ["reportDataFilename", ""],
    ["reportDataYAML", ""],
    ["reportDataJSON", {}],
    ["groupData", {
        "project_title": "",
        "question_a": "",
        "question_b": "",
        "group": null,
        "members": null
    }]
];

const abgridDataStore = (Alpine) => ({
    
    ...initState(stateFn, Alpine, "_data"),

    get groupDataIsDirty() {
        return Object
            .values(this.groupData)
            .filter(Boolean)
            .reduce((acc, itr) => acc + !!itr, 0) > 0
    },

    get groupDataIsComplete() {
        return Object
            .values(this.groupData)
            .filter(Boolean)
            .reduce((acc, itr) => acc + !!itr, 0) == Object.keys(this.groupData).length
    },

    resetGroupData() {
        this.wipeState(["groupData"]);
    },

    wipeState(resetProps = null) {
        wipeState.call(this, stateFn, resetProps);
    },
});

export { abgridDataStore };
