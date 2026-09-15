/** React Router's optional view-transition cache must never reach browser storage. */
export function routerWindow(): Window {
  const ephemeralStorage: Storage = {
    length: 0,
    clear() {},
    getItem() { return null; },
    key() { return null; },
    removeItem() {},
    setItem() {},
  };
  return new Proxy(window, {
    get(target, property): unknown {
      if (property === 'sessionStorage' || property === 'localStorage') return ephemeralStorage;
      const value: unknown = Reflect.get(target, property, target);
      return typeof value === 'function' ? value.bind(target) as unknown : value;
    },
  });
}
