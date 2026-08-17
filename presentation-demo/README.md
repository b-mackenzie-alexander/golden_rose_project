# Golden Rose Synthetic Presentation Demo

This is a local-only concept demonstration using fictional synthetic data.
It is not Golden Rose product code, a production deployment, an authentication implementation, or a client-data system.

## What this is

A static, local-only demo that shows one guided workflow:

- Agency operations dashboard
- Staff request workspace
- Manual worker/employer intake with synthetic shared-queue drafts
- Worker opportunity view with an interest-request preview
- Employer status view with a richer request-status and update preview
- Basic English/Spanish page translation toggle for stakeholder review

No API calls, no databases, no authentication, no cloud services, and no client/real data are used.

## Run locally (primary path)

```bash
python3 -m http.server 4173 --bind 127.0.0.1 --directory presentation-demo
```

Open:

- http://127.0.0.1:4173/

Use keyboard navigation (Tab/Enter/Space), the top navigation, the visible request/action controls, and the language toggle in the banner. The agency dashboard request cards open the detail view, the Add records view demonstrates paper-to-draft worker/employer intake, and the worker/employer views each include one synthetic preview action.

## Run tests (artifact-local)

```bash
node --test presentation-demo/app.test.mjs
```

## Serve with Docker (loopback only)

### Build

```bash
docker build -t golden-rose-presentation-demo:local presentation-demo
```

### Run

```bash
docker run --rm --name golden-rose-presentation-demo -p 127.0.0.1:4173:8080 golden-rose-presentation-demo:local
```

In a separate terminal, verify the served artifact:

```bash
node presentation-demo/verify-served-demo.mjs http://127.0.0.1:4173
```

### Stop

Press Ctrl+C in the container terminal and confirm no matching container remains:

```bash
docker ps --filter name=golden-rose-presentation-demo
```

## No external services

This demo intentionally does not use:

- Cloud services
- Database
- API endpoints
- Client credentials
- Real employer or worker data
- Deployment tooling

A browser refresh returns the demo to its initial synthetic state.
