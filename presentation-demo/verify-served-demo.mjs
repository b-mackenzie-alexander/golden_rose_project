const requiredBanner =
  "Concept demonstration — fictional synthetic data — local presentation only.";

const requiredViews = [
  "Agency operations dashboard",
  "Request detail and staff coordination",
  "Manual worker and employer intake",
  "Worker opportunity view",
  "Employer request status view",
];

const requiredInteractionCopy = [
  "Today 14:30",
  "Open request overview",
  "My work today",
  "Open searches",
  "Open until filled",
  "Full-time office administrator search",
  "Add synthetic employer draft",
  "Add synthetic worker draft",
  "Open worker request page",
  "Open interest request",
  "Open update preview",
  "Assign to me",
  "Mark review complete",
  "Waiting on employer",
  "Prepare worker outreach",
  "data-set-locale=\"en\"",
  "data-set-locale=\"es\"",
  "Panel operativo de la agencia",
  "Mi trabajo de hoy",
  "Búsquedas abiertas",
  "Registro manual de trabajadores y empleadores",
  "Abrir solicitud de interés",
];

function fail(message) {
  console.error(message);
  process.exitCode = 1;
}

function ensureLoopback(url) {
  const parsed = new URL(url);
  const allowed = new Set(["127.0.0.1", "localhost", "::1"]);
  if (!allowed.has(parsed.hostname)) {
    fail(`verify-served-demo requires loopback host only; got ${parsed.hostname}`);
    return false;
  }
  return true;
}

function containsAll(content, items) {
  return items.every((value) => content.includes(value));
}

async function main() {
  const url = process.argv[2];
  if (!url) {
    fail("Usage: node presentation-demo/verify-served-demo.mjs <http://127.0.0.1:4173>");
    return;
  }

  if (!ensureLoopback(url)) {
    return;
  }

  const rootResponse = await fetch(url);
  if (!rootResponse.ok) {
    fail(`Root request failed with status ${rootResponse.status}`);
    return;
  }

  const rootHtml = await rootResponse.text();

  const appJsResponse = await fetch(new URL("./app.js", `${url}/`).toString());
  if (!appJsResponse.ok) {
    fail(`app.js request failed with status ${appJsResponse.status}`);
    return;
  }

  const appJsText = await appJsResponse.text();
  const combined = `${rootHtml}\n${appJsText}`;

  if (!combined.includes(requiredBanner)) {
    fail("Persistent demo banner not found in served artifacts.");
    return;
  }

  if (!containsAll(combined, requiredViews)) {
    fail("Not all required view labels are present in served artifacts.");
    return;
  }

  if (!containsAll(combined, requiredInteractionCopy)) {
    fail("Not all required interaction or translation labels are present in served artifacts.");
    return;
  }

  console.log("Served demo artifact verification passed.");
}

main().catch((error) => {
  fail(error instanceof Error ? error.message : String(error));
});
