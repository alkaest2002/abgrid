export const initState = (stateFn, Alpine, prefix) => {
  return stateFn().reduce(
    (acc, [key, defaultValue]) => ({
      ...acc,
      ...{
        [key]: Alpine.$persist(defaultValue)
          .using(localStorage)
          .as(`xxx_${prefix}_${key}`),
      },
    }),
    {},
  );
};

export function exportState(stateFn, rootKey) {
  const data = stateFn()
    .map(([key, _]) => key)
    .reduce((acc, itr) => ({ ...acc, ...{ [itr]: this[itr] } }), {});
  return { [rootKey]: data };
}

export function importState(dataJSON) {
  this.wipeState();
  for (const [key, value] of Object.entries(dataJSON)) {
    this[key] !== undefined && (this[key] = value);
  }
}

export function wipeState(stateFn, omitProps) {
  stateFn().forEach(([key, defaultValue]) => {
    this[key] = omitProps.includes(key) ? this[key] : defaultValue;
  });
}
