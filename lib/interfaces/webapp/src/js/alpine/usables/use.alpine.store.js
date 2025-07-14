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
