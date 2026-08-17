import assert from "node:assert/strict";
import { test } from "node:test";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import {
  DEMO_NOTICE,
  DEMO_DATA,
  VIEWS,
  validateDemoContract,
  createInitialDemoState,
  recordFictionalFollowUp,
  selectRequest,
  addSyntheticIntakeRecord,
  openWorkerInterest,
  openEmployerUpdate,
  renderViewMarkup,
} from "./app.js";

const FORBIDDEN_DECISION_TERMS = ["matched", "recommended", "eligible", "hire"];
const TEST_FILE_DIR = path.dirname(fileURLToPath(import.meta.url));

function collectCopyStrings(value, out = []) {
  if (typeof value === "string") {
    out.push(value);
    return out;
  }

  if (value == null) {
    return out;
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      collectCopyStrings(item, out);
    }
    return out;
  }

  if (typeof value === "object") {
    for (const key of Object.keys(value)) {
      collectCopyStrings(value[key], out);
    }
    return out;
  }

  return out;
}

function hasBannedTerms(values) {
  const joined = values.join(" ").toLowerCase();
  return FORBIDDEN_DECISION_TERMS.find((term) => new RegExp(`\\b${term}\\b`, "i").test(joined));
}

function hasLikelyAddress(values) {
  const joined = values.join(" \n").toLowerCase();
  const addressPattern = /\b\d+\s+[^\n,]+\b(street|st|road|rd|avenue|ave|lane|ln|drive|dr|court|ct|way|place|blvd|boulevard)\b/i;
  return addressPattern.test(joined);
}

test("demo notice and synthetic data contract is stable and safe", () => {
  assert.match(DEMO_NOTICE, /fictional synthetic data/i);
  assert.equal(DEMO_NOTICE.includes("not a production system"), false);

  assert.equal(DEMO_DATA.employerName, "Harbor & Pine Hospitality");
  assert.equal(DEMO_DATA.serviceArea, "Downtown service area");
  assert.equal(DEMO_DATA.worker.displayName, "Jordan R.");
  assert.equal(DEMO_DATA.worker.actionText, "Open interest request");
  assert.equal(DEMO_DATA.requests.length, 3);
  assert.ok(DEMO_DATA.requests.every((request) => /\b(Today|Tomorrow) \d{2}:\d{2}\b/.test(request.due)));

  const copyValues = [DEMO_NOTICE, ...collectCopyStrings(VIEWS), ...collectCopyStrings(DEMO_DATA)];
  assert.equal(hasBannedTerms(copyValues), undefined);
  assert.equal(hasLikelyAddress(copyValues), false);

  const violations = validateDemoContract();
  assert.equal(violations.length, 0, JSON.stringify(violations, null, 2));
});

test("index.html has working shell structure without repeated disclaimer footer", async () => {
  const indexPath = path.join(TEST_FILE_DIR, "index.html");
  const indexHtml = await readFile(indexPath, "utf8");

  assert.match(indexHtml, /<html\s+lang="en"/i);
  assert.equal((indexHtml.match(/<main\b/g) || []).length, 1);
  assert.equal((indexHtml.match(/Concept demonstration — fictional synthetic data — local presentation only\./g) || []).length, 1);
  assert.equal(indexHtml.includes("<footer"), false);
  assert.match(indexHtml, /aria-label="Demo views"/);
  assert.match(indexHtml, /role="status"/);
  assert.match(indexHtml, /type="module"\s+src="\.\/app\.js"/);
  assert.match(indexHtml, /Agency dashboard/);
  assert.match(indexHtml, /Request detail/);
  assert.match(indexHtml, /Add records/);
});

test("dashboard renders actionable cards with concrete due times and detail entry points", () => {
  const state = createInitialDemoState();
  const dashboard = renderViewMarkup(state, "dashboard");

  assert.equal(dashboard.viewId, "dashboard");
  assert.match(dashboard.content, /open employer requests/);
  assert.match(dashboard.content, /Due Today 14:30/);
  assert.match(dashboard.content, /Due Today 16:00/);
  assert.match(dashboard.content, /Due Tomorrow 09:30/);
  assert.equal((dashboard.content.match(/data-select-request=/g) || []).length, 3);
  assert.match(dashboard.content, /Open full request detail/);
  assert.match(dashboard.content, /Add worker or employer/);
  assert.match(dashboard.content, /Preview worker view/);
  assert.match(dashboard.content, /Preview employer view/);
});

test("request selection changes the agency detail page", () => {
  const baseState = createInitialDemoState();
  const nextState = selectRequest(baseState, "req-pine-event-setup");
  const workspace = renderViewMarkup(nextState, "workspace");

  assert.match(workspace.content, /Event setup support/);
  assert.match(workspace.content, /Today 16:00/);
  assert.match(workspace.content, /Back-of-house Support/);
  assert.match(workspace.content, /Add worker or employer/);
  assert.match(workspace.content, /Open worker request page/);
  assert.match(workspace.content, /Open employer status page/);
});

test("manual intake view demonstrates staff-added worker and employer draft records", () => {
  const baseState = createInitialDemoState();
  const initialIntake = renderViewMarkup(baseState, "intake");

  assert.equal(initialIntake.viewTitle, "Manual worker and employer intake");
  assert.match(initialIntake.content, /Manual record intake/);
  assert.match(initialIntake.content, /Add synthetic employer draft/);
  assert.match(initialIntake.content, /Add synthetic worker draft/);
  assert.match(initialIntake.content, /No synthetic records have been added yet/);

  const afterEmployer = addSyntheticIntakeRecord(baseState, "employer");
  assert.equal(afterEmployer.intakeRecords.length, 1);
  assert.match(afterEmployer.workspace.confirmationMessage, /Employer draft added/);

  const afterWorker = addSyntheticIntakeRecord(afterEmployer, "worker");
  assert.equal(afterWorker.intakeRecords.length, 2);
  assert.match(afterWorker.workspace.confirmationMessage, /Worker draft added/);

  const duplicate = addSyntheticIntakeRecord(afterWorker, "worker");
  assert.equal(duplicate.intakeRecords.length, 2);
  assert.match(duplicate.workspace.confirmationMessage, /already in the shared staff queue/);

  const filledIntake = renderViewMarkup(afterWorker, "intake");
  assert.match(filledIntake.content, /Harbor Annex Events/);
  assert.match(filledIntake.content, /Camila R\./);
  assert.match(filledIntake.content, /shared staff queue/);
  assert.match(filledIntake.content, /another workstation/);
});

test("state helpers support one staff follow-up action and reset contract", () => {
  const baseState = createInitialDemoState();
  const baselineSnapshot = JSON.stringify(DEMO_DATA);

  assert.equal(baseState.workspace.timeline.length, 4);
  assert.equal(baseState.workspace.followUpRecorded, false);
  assert.equal(baseState.workspace.confirmationMessage, null);

  const afterFollowUp = recordFictionalFollowUp(baseState);
  assert.notEqual(afterFollowUp, baseState);
  assert.equal(afterFollowUp.workspace.followUpRecorded, true);
  assert.equal(afterFollowUp.workspace.timeline.length, baseState.workspace.timeline.length + 1);
  assert.match(afterFollowUp.workspace.confirmationMessage, /Staff follow-up displayed/i);
  assert.equal(JSON.stringify(DEMO_DATA), baselineSnapshot);

  const duplicate = recordFictionalFollowUp(afterFollowUp);
  assert.equal(duplicate.workspace.timeline.length, afterFollowUp.workspace.timeline.length);
  assert.equal(duplicate.workspace.followUpRecorded, true);
  assert.match(duplicate.workspace.confirmationMessage, /already shown/i);
});

test("view metadata remains bounded to exactly five presentation views", () => {
  const ids = Object.keys(VIEWS);
  assert.deepEqual(ids.sort(), ["dashboard", "employer", "intake", "worker", "workspace"].sort());
});

test("worker and employer views include interactive preview states", () => {
  const state = createInitialDemoState();

  const worker = renderViewMarkup(state, "worker");
  assert.equal(worker.viewTitle, "Worker opportunity view");
  assert.match(worker.content, /Open interest request/);
  assert.equal(worker.content.includes("What the worker would review next"), false);

  const workerOpened = renderViewMarkup(openWorkerInterest(state), "worker");
  assert.match(workerOpened.content, /What the worker would review next/);
  assert.match(workerOpened.content, /Coordinator contacts the worker for a human-reviewed conversation/);

  const employer = renderViewMarkup(state, "employer");
  assert.equal(employer.viewTitle, "Employer request status view");
  assert.match(employer.content, /Visible milestone trail/);
  assert.match(employer.content, /Employer-safe request summary/);
  assert.equal(employer.content.includes(DEMO_DATA.worker.displayName), false);

  const employerOpened = renderViewMarkup(openEmployerUpdate(state), "employer");
  assert.match(employerOpened.content, /Next update visible to employer/);
  assert.match(employerOpened.content, /No worker identity, exact address, or private contact information is exposed here/);

  const postValidation = validateDemoContract();
  assert.equal(postValidation.length, 0);
});
