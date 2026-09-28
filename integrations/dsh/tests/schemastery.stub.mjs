// A stand-in for `@deepseek-ai/schemastery`, for tests only.
//
// The real package is a peer dependency the profile provides — it is deliberately not a
// dependency of this package, because the host supplies it and there must be exactly one copy
// on the resolve path. That leaves the unit tests unable to import `entry.js` at all, which is
// why `resolve-hook.mjs` points the specifier here.
//
// It is not a reimplementation. It records just enough of a schema for the tests to assert the
// thing that actually matters: that the settings section declares exactly the keys both halves
// agree on, with the defaults the browser half ships.

function make(kind) {
  return {
    __kind: kind,
    default(value) {
      return { __kind: kind, __default: value }
    },
  }
}

export default {
  boolean: () => make('boolean'),
  string: () => make('string'),
  number: () => make('number'),
  object: (spec) => ({ __kind: 'object', __spec: spec }),
}
