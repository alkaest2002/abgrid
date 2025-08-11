/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
import { initState, wipeState } from "../usables/use.alpine.store.js";
import { createEmptyGroupData, createEmptyYamlParseError } from "./models.js";

const stateFn = () => [
    ["dataFilename", ""],
    ["dataYAML", ""],
    ["dataYAMLError", createEmptyYamlParseError()],
    ["dataGroup", createEmptyGroupData()]
];

export const dataStore = (Alpine) => ({
    
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

    resetDataYaml() {
        this.wipeState(["dataYAML", "dataYAMLError", "dataFilename"]);
    },

    resetdDataGroup() {
        this.wipeState(["dataGroup"]);
    },

    wipeState(resetProps = []) {
        wipeState(this, stateFn, resetProps);
    },
});