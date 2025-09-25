/*
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
*/
export const initState = (stateFn, Alpine, prefix) => {
    return stateFn().reduce(
        (acc, [key, defaultValue, shouldPersist = true]) => ({
            ...acc,
            ...{
                [key]: shouldPersist
                    ? Alpine.$persist(defaultValue).using(localStorage).as(`xxx_${prefix}_${key}`)
                    : defaultValue,
            },
        }),
        {},
    );
};

export const wipeState = (store, stateFn, resetProps = []) => {
    if (resetProps.length == 0) {
        stateFn().forEach(([key, defaultValue]) => {
            store[key] = defaultValue;
        });
    }
    stateFn().forEach(([key, defaultValue]) => {
        store[key] = resetProps.includes(key) ? defaultValue : store[key];
    });
}
