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

export const wipeState = (stateFn, omitProps) => {
  stateFn().forEach(([key, defaultValue]) => {
    this[key] = omitProps.includes(key) ? this[key] : defaultValue;
  });
}
