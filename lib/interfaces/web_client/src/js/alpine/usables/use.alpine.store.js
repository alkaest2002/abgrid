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

export function wipeState(stateFn, resetProps = null) {
  if (!resetProps) {
    stateFn().forEach(([key, defaultValue]) => {
      this[key] = defaultValue;
    });
  }
  stateFn().forEach(([key, defaultValue]) => {
    this[key] = resetProps.includes(key) ? defaultValue : this[key];
  });
}
