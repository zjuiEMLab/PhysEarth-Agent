// A resolver hook that redirects one bare specifier to a local stub.
//
// Used by `host.test.mjs` (see `schemastery.stub.mjs` for why) and by nothing else. A hook
// rather than a shim in `node_modules/` on purpose: a stub inside this package would be found
// before the host's real copy when the plugin is installed, and would shadow it.

const STUB = new URL('./schemastery.stub.mjs', import.meta.url).href

export async function resolve(specifier, context, nextResolve) {
  if (specifier === '@deepseek-ai/schemastery') {
    return { url: STUB, shortCircuit: true, format: 'module' }
  }
  return nextResolve(specifier, context)
}
