# aura-web

A real web client for the canonical AURA API. Every value displayed is fetched
live from a running `aura-api` server; no demo data or hardcoded dashboard
metrics are injected anywhere.

## Features

- **Status** — live `/health`, `/ready`, `/v1/metrics` (real counters/gauges/latency)
- **Reasoning console** — ask questions against `/v1/reason`, see the structured answer
- **Memory** — write (`/v1/remember`) and search (`/v1/recall`) memory records
- **Knowledge** — add claims (`/v1/observe`) and retrieve them (`/v1/retrieve`)
- **Research** — run an evidence-aware research cycle (`/v1/research`)
- **Audit** — security/decision events from the canonical audit log (`/v1/audit`)
- **Settings** — configure endpoint and optional API key

## Security

- The API key is stored only in `sessionStorage`, never in `localStorage`, and
  is cleared when the tab closes. It is never logged or rendered.
- Requests carry an `Authorization: Bearer` header only when a key is set.
- Timeouts and bounded retries apply to every request; server-side secret
  redaction is enforced server-side by `aura-api`.

## Development

```bash
npm install
npm run dev     # vite dev server (proxy to AURA API via the endpoint setting)
npm run build   # tsc -b && vite build
npm run lint    # eslint
npm test        # vitest (jsdom)
```

Point a server at `http://127.0.0.1:8765` (the default):

```bash
cd ../aura && python -m aura.api.server
```

Then open the Vite dev URL and use the **Settings** tab to connect if your
server uses a different endpoint or an API key.

## Architecture

`src/lib/api.ts` is the typed API client (fetch, timeout, retry, typed errors).
`src/lib/settings.tsx` + `settings-context.ts` hold endpoint/key state with the
secure storage strategy. Pages are thin components over the API client, and
every render path consumes live API data.