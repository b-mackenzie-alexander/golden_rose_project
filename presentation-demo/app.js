export const DEMO_NOTICE =
  "Concept demonstration — fictional synthetic data — local presentation only.";

export const VIEWS = Object.freeze({
  dashboard: Object.freeze({
    id: "dashboard",
    navLabel: "Agency dashboard",
    pageTitle: "Agency operations dashboard",
  }),
  workspace: Object.freeze({
    id: "workspace",
    navLabel: "Request detail",
    pageTitle: "Request detail and staff coordination",
  }),
  intake: Object.freeze({
    id: "intake",
    navLabel: "Add records",
    pageTitle: "Manual worker and employer intake",
  }),
  worker: Object.freeze({
    id: "worker",
    navLabel: "Worker view",
    pageTitle: "Worker opportunity view",
  }),
  employer: Object.freeze({
    id: "employer",
    navLabel: "Employer view",
    pageTitle: "Employer request status view",
  }),
});

const DEMO_VIEW_SEQUENCE = Object.freeze([
  VIEWS.dashboard.id,
  VIEWS.workspace.id,
  VIEWS.intake.id,
  VIEWS.worker.id,
  VIEWS.employer.id,
]);

const DEMO_EVENTS = Object.freeze([
  Object.freeze({
    id: "req-harbor-cleaning",
    label: "Same-day coverage request",
    status: "Needs staff review",
    owner: "Priya K.",
    employerName: "Harbor & Pine Hospitality",
    serviceArea: "Downtown service area",
    due: "Today 14:30",
    serviceWindow: "Fri 17:00-21:00",
    role: "General Cleaner",
    count: 2,
    urgency: "High",
    source: "Employer message at 09:12",
    summary: "Two evening cleaning staff requested for a banquet reset window after a late event update.",
    nextStep: "Confirm scope, prepare worker-safe summary, and schedule outreach before 14:30.",
    coordinatorNote: "Employer can accept staggered arrivals if the agency confirms the first person by 15:30.",
    workerSafeSummary:
      "Evening cleaning support in the downtown service area. Tasks include room reset, supply restock, and light closing support.",
    employerVisibleStatus: "Agency reviewing coverage options",
  }),
  Object.freeze({
    id: "req-pine-event-setup",
    label: "Event setup support",
    status: "Coverage in progress",
    owner: "Marisol R.",
    employerName: "Harbor & Pine Hospitality",
    serviceArea: "Central service area",
    due: "Today 16:00",
    serviceWindow: "Sat 10:00-14:00",
    role: "Back-of-house Support",
    count: 1,
    urgency: "Medium",
    source: "Phone intake at 10:03",
    summary: "One back-of-house support worker requested for staging, supply movement, and event room turnover.",
    nextStep: "Confirm physical requirements and prepare the employer-facing status update.",
    coordinatorNote: "Ask employer to confirm whether supply carts are available before final outreach.",
    workerSafeSummary: "Short Saturday setup support in the central service area with staging and room-turnover tasks.",
    employerVisibleStatus: "Details being confirmed",
  }),
  Object.freeze({
    id: "req-harbor-followup",
    label: "Employer follow-up due",
    status: "Awaiting update",
    owner: "Priya K.",
    employerName: "Harbor & Pine Hospitality",
    serviceArea: "Downtown service area",
    due: "Tomorrow 09:30",
    serviceWindow: "Next week schedule review",
    role: "Recurring cleaning support",
    count: 3,
    urgency: "Routine",
    source: "Standing account cadence",
    summary: "Recurring support forecast needs a staff check-in before the next weekly request cycle.",
    nextStep: "Confirm forecasted dates and update the employer status trail.",
    coordinatorNote: "Keep this as a planning conversation; do not expose worker identities in the employer view.",
    workerSafeSummary: "Recurring support forecast; details are not ready for worker-facing outreach yet.",
    employerVisibleStatus: "Follow-up scheduled",
  }),
]);

const STAFF_ACTIVITY = Object.freeze([
  "09:12 — Employer request received and triaged into staff review.",
  "09:34 — Coordinator added service-window notes and broad area only.",
  "10:03 — Second request grouped under the same employer workspace.",
  "10:28 — Worker-safe summary drafted for the same-day request.",
]);

const EMPLOYER_MILESTONES = Object.freeze([
  Object.freeze({ label: "Request received", when: "09:12", note: "Agency has the staffing request." }),
  Object.freeze({ label: "Scope review", when: "10:28", note: "Service window and task summary are being checked." }),
  Object.freeze({ label: "Coordinator outreach", when: "14:30", note: "Next visible update is scheduled for this afternoon." }),
]);

const INTAKE_TEMPLATES = Object.freeze({
  employer: Object.freeze({
    id: "employer-draft-harbor-annex",
    type: "Employer",
    name: "Harbor Annex Events",
    source: "Paper intake sheet",
    capturedBy: "Front desk staff",
    status: "Draft saved for staff review",
    continuityNote: "Visible in the shared staff queue after entry.",
  }),
  worker: Object.freeze({
    id: "worker-draft-camila-r",
    type: "Worker",
    name: "Camila R.",
    source: "Walk-in registration packet",
    capturedBy: "Front desk staff",
    status: "Draft saved for staff review",
    continuityNote: "Available for agency follow-up from another workstation.",
  }),
});

export const DEMO_DATA = Object.freeze({
  employerName: "Harbor & Pine Hospitality",
  serviceArea: "Downtown service area",
  requestedBy: "Harbor Team",
  owner: "Priya K.",
  requestStatus: "Needs staff review",
  worker: Object.freeze({
    displayName: "Jordan R.",
    preferredShift: "Day shift",
    actionText: "Open interest request",
  }),
  requests: DEMO_EVENTS,
  staffActivity: STAFF_ACTIVITY,
  employerMilestones: EMPLOYER_MILESTONES,
  intakeTemplates: INTAKE_TEMPLATES,
});

const FORBIDDEN_DECISION_TERMS = ["matched", "recommended", "eligible", "hire"];

function collectCopyStrings(value, out = []) {
  if (typeof value === "string") {
    out.push(value);
    return out;
  }
  if (value == null) return out;
  if (Array.isArray(value)) {
    for (const item of value) collectCopyStrings(item, out);
    return out;
  }
  if (typeof value === "object") {
    for (const key of Object.keys(value)) collectCopyStrings(value[key], out);
  }
  return out;
}

function getRequestById(requestId) {
  return DEMO_DATA.requests.find((request) => request.id === requestId) ?? DEMO_DATA.requests[0];
}

export function validateDemoContract() {
  const violations = [];
  const noticeNormalized = DEMO_NOTICE.toLowerCase();

  if (!noticeNormalized.includes("fictional synthetic data")) {
    violations.push("DEMO_NOTICE must include 'fictional synthetic data'.");
  }

  if (!VIEWS.dashboard || !VIEWS.workspace || !VIEWS.intake || !VIEWS.worker || !VIEWS.employer) {
    violations.push("All five views must exist: dashboard, workspace, intake, worker, employer.");
  }

  if (DEMO_DATA.requests.length !== 3) {
    violations.push("Demo dashboard must include exactly three agency request cards.");
  }

  if (!DEMO_DATA.requests.every((request) => request.due.match(/\b(Today|Tomorrow) \d{2}:\d{2}\b/))) {
    violations.push("Every request card must include a concrete due time.");
  }

  if (DEMO_DATA.worker.actionText !== "Open interest request") {
    violations.push("Worker action text must be exactly 'Open interest request'.");
  }

  const copy = [DEMO_NOTICE, ...collectCopyStrings(VIEWS), ...collectCopyStrings(DEMO_DATA)];
  const concatenated = copy.join("\n").toLowerCase();

  for (const term of FORBIDDEN_DECISION_TERMS) {
    const forbiddenMatch = new RegExp(`\\b${term}\\b`, "i");
    if (forbiddenMatch.test(concatenated)) {
      violations.push(`Contract text must not include decision term: ${term}`);
    }
  }

  const addressPattern = /\b\d+\s+[^\n,]+\b(street|st|road|rd|avenue|ave|lane|ln|drive|dr|court|ct|way|place|blvd|boulevard)\b/i;
  if (addressPattern.test(concatenated)) {
    violations.push("Demo copy must not include street-like address text.");
  }

  return violations;
}

export function createInitialDemoState() {
  return {
    activeView: VIEWS.dashboard.id,
    selectedRequestId: DEMO_DATA.requests[0].id,
    workerInterestOpened: false,
    employerUpdateOpened: false,
    intakeRecords: [],
    workspace: {
      followUpRecorded: false,
      confirmationMessage: null,
      timeline: [...DEMO_DATA.staffActivity],
    },
  };
}

export function recordFictionalFollowUp(state) {
  const selectedRequest = getRequestById(state.selectedRequestId);
  const workspace = state.workspace ?? createInitialDemoState().workspace;

  if (workspace.followUpRecorded) {
    return {
      ...state,
      workspace: {
        ...workspace,
        followUpRecorded: true,
        confirmationMessage: "Follow-up is already shown in this presentation run; refresh resets the synthetic state.",
      },
    };
  }

  return {
    ...state,
    workspace: {
      ...workspace,
      followUpRecorded: true,
      confirmationMessage: `Staff follow-up displayed for ${selectedRequest.label}.`,
      timeline: [
        ...workspace.timeline,
        `Current run — staff follow-up displayed for ${selectedRequest.label} before ${selectedRequest.due}.`,
      ],
    },
  };
}

function ensureValidViewId(viewId) {
  return DEMO_VIEW_SEQUENCE.includes(viewId) ? viewId : VIEWS.dashboard.id;
}

export function selectRequest(state, requestId) {
  const selectedRequest = getRequestById(requestId);
  return { ...state, selectedRequestId: selectedRequest.id };
}

export function openWorkerInterest(state) {
  return { ...state, workerInterestOpened: true };
}

export function openEmployerUpdate(state) {
  return { ...state, employerUpdateOpened: true };
}

export function addSyntheticIntakeRecord(state, recordType) {
  const template = DEMO_DATA.intakeTemplates[recordType];
  if (!template) return state;

  const intakeRecords = state.intakeRecords ?? [];
  const alreadyAdded = intakeRecords.some((record) => record.id === template.id);
  if (alreadyAdded) {
    return {
      ...state,
      workspace: {
        ...state.workspace,
        confirmationMessage: `${template.type} draft is already in the shared staff queue for this presentation run.`,
      },
    };
  }

  return {
    ...state,
    intakeRecords: [...intakeRecords, template],
    workspace: {
      ...state.workspace,
      confirmationMessage: `${template.type} draft added to the shared staff queue.`,
      timeline: [
        ...state.workspace.timeline,
        `Current run — ${template.type.toLowerCase()} draft entered from ${template.source}.`,
      ],
    },
  };
}

export function renderViewMarkup(state, viewId = state.activeView) {
  const resolvedViewId = ensureValidViewId(viewId);
  const selectedRequest = getRequestById(state.selectedRequestId);
  const activeView = {
    dashboard: () => renderDashboardMarkup(state, selectedRequest),
    workspace: () => renderWorkspaceMarkup(state, selectedRequest),
    intake: () => renderIntakeMarkup(state),
    worker: () => renderWorkerMarkup(state, selectedRequest),
    employer: () => renderEmployerMarkup(state, selectedRequest),
  };

  return {
    viewId: resolvedViewId,
    viewTitle: VIEWS[resolvedViewId].pageTitle,
    content: activeView[resolvedViewId](),
  };
}

function renderMetricCards() {
  return `
    <section class="metric-grid" aria-label="Agency workflow metrics">
      <article class="metric-card"><span class="metric-value">3</span><span class="metric-label">open employer requests</span></article>
      <article class="metric-card"><span class="metric-value">14:30</span><span class="metric-label">next staff deadline</span></article>
      <article class="metric-card"><span class="metric-value">2</span><span class="metric-label">audience views ready</span></article>
      <article class="metric-card"><span class="metric-value">2</span><span class="metric-label">paper records ready to enter</span></article>
    </section>
  `;
}

function renderRequestCard(request, selectedRequestId) {
  const selected = request.id === selectedRequestId;
  return `
    <article class="request-card ${selected ? "selected-card" : ""}" aria-labelledby="${request.id}-heading">
      <div class="card-topline">
        <span class="status-pill ${request.urgency === "High" ? "status-warning" : request.urgency === "Medium" ? "status-open" : "status-pending"}">${request.urgency}</span>
        <span class="due-chip">Due ${request.due}</span>
      </div>
      <h2 id="${request.id}-heading">${request.label}</h2>
      <p>${request.summary}</p>
      <dl class="compact-details">
        <div><dt>Role</dt><dd>${request.role}</dd></div>
        <div><dt>Window</dt><dd>${request.serviceWindow}</dd></div>
        <div><dt>Owner</dt><dd>${request.owner}</dd></div>
      </dl>
      <button type="button" class="secondary-btn full-width" data-select-request="${request.id}" data-switch="workspace">
        Open request overview
      </button>
    </article>
  `;
}

function renderDashboardMarkup(state, selectedRequest) {
  return `
    ${renderMetricCards()}
    <section class="dashboard-layout" aria-label="Agency dashboard content">
      <div class="request-list" aria-label="Actionable request cards">
        ${DEMO_DATA.requests.map((request) => renderRequestCard(request, state.selectedRequestId)).join("")}
      </div>
      <aside class="detail-panel" aria-label="Selected request quick detail">
        <p class="eyebrow">Selected request</p>
        <h2>${selectedRequest.label}</h2>
        <p>${selectedRequest.summary}</p>
        <dl class="detail-list">
          <div><dt>Employer</dt><dd>${selectedRequest.employerName}</dd></div>
          <div><dt>Broad area</dt><dd>${selectedRequest.serviceArea}</dd></div>
          <div><dt>Due</dt><dd>${selectedRequest.due}</dd></div>
          <div><dt>Status</dt><dd>${selectedRequest.status}</dd></div>
          <div><dt>Next staff step</dt><dd>${selectedRequest.nextStep}</dd></div>
        </dl>
        <div class="button-row">
          <button type="button" class="primary-btn" data-switch="workspace">Open full request detail</button>
          <button type="button" class="secondary-btn" data-switch="intake">Add worker or employer</button>
          <button type="button" class="secondary-btn" data-switch="worker">Preview worker view</button>
          <button type="button" class="secondary-btn" data-switch="employer">Preview employer view</button>
        </div>
      </aside>
    </section>
  `;
}

function renderTimeline(timeline) {
  return `
    <ol class="timeline-list">
      ${timeline
        .map(
          (entry, index) => `
            <li><span class="timeline-index">${index + 1}</span><span>${entry}</span></li>
          `,
        )
        .join("")}
    </ol>
  `;
}

function renderIntakeQueue(records) {
  if (records.length === 0) {
    return `<p class="empty-state">No synthetic records have been added yet. Use the intake actions to show how paper records become shared staff-visible drafts.</p>`;
  }

  return `
    <div class="queue-list">
      ${records
        .map(
          (record) => `
            <article class="queue-card">
              <p class="eyebrow">${record.type} draft</p>
              <h3>${record.name}</h3>
              <dl class="detail-list">
                <div><dt>Source</dt><dd>${record.source}</dd></div>
                <div><dt>Captured by</dt><dd>${record.capturedBy}</dd></div>
                <div><dt>Status</dt><dd>${record.status}</dd></div>
                <div><dt>Continuity</dt><dd>${record.continuityNote}</dd></div>
              </dl>
            </article>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderIntakeMarkup(state) {
  const intakeRecords = state.intakeRecords ?? [];
  return `
    <section class="workspace-hero">
      <div>
        <p class="eyebrow">First rollout workflow</p>
        <h2>Manual record intake</h2>
        <p>Staff can turn paper employer sheets and worker registration packets into shared draft records without needing a finished public portal.</p>
      </div>
      <dl class="deadline-card">
        <div><dt>Current paper backlog</dt><dd>2 starter records</dd></div>
        <div><dt>Continuity shown</dt><dd>Shared staff queue concept</dd></div>
        <div><dt>Live database</dt><dd>Not connected in this demo</dd></div>
      </dl>
    </section>

    <section class="two-column" aria-label="Manual intake actions">
      <article class="action-card">
        <h2>Add employer from paper</h2>
        <p>Use a synthetic paper-intake example to create an employer draft that another staff member could continue reviewing.</p>
        <dl class="detail-list">
          <div><dt>Name</dt><dd>${DEMO_DATA.intakeTemplates.employer.name}</dd></div>
          <div><dt>Source</dt><dd>${DEMO_DATA.intakeTemplates.employer.source}</dd></div>
          <div><dt>Review state</dt><dd>${DEMO_DATA.intakeTemplates.employer.status}</dd></div>
        </dl>
        <button type="button" class="primary-btn" data-action="add-employer-record">Add synthetic employer draft</button>
      </article>

      <article class="action-card">
        <h2>Add worker from packet</h2>
        <p>Use a synthetic walk-in packet to create a worker draft that stays agency-reviewed before any outreach.</p>
        <dl class="detail-list">
          <div><dt>Name</dt><dd>${DEMO_DATA.intakeTemplates.worker.name}</dd></div>
          <div><dt>Source</dt><dd>${DEMO_DATA.intakeTemplates.worker.source}</dd></div>
          <div><dt>Review state</dt><dd>${DEMO_DATA.intakeTemplates.worker.status}</dd></div>
        </dl>
        <button type="button" class="primary-btn" data-action="add-worker-record">Add synthetic worker draft</button>
      </article>
    </section>

    <section class="timeline" aria-label="Shared staff queue preview">
      <h2>Shared staff queue preview</h2>
      ${renderIntakeQueue(intakeRecords)}
      <div class="button-row inline-actions">
        <button type="button" class="secondary-btn" data-switch="dashboard">Back to agency dashboard</button>
        <button type="button" class="secondary-btn" data-switch="workspace">Open request detail</button>
      </div>
    </section>
  `;
}

function renderWorkspaceMarkup(state, selectedRequest) {
  return `
    <section class="workspace-hero">
      <div>
        <p class="eyebrow">Agency-owned request detail</p>
        <h2>${selectedRequest.label}</h2>
        <p>${selectedRequest.summary}</p>
      </div>
      <dl class="deadline-card">
        <div><dt>Due</dt><dd>${selectedRequest.due}</dd></div>
        <div><dt>Service window</dt><dd>${selectedRequest.serviceWindow}</dd></div>
        <div><dt>Coordinator</dt><dd>${selectedRequest.owner}</dd></div>
      </dl>
    </section>

    <section class="two-column" aria-label="Request detail sections">
      <article class="action-card">
        <h2>Staff coordination detail</h2>
        <dl class="detail-list">
          <div><dt>Employer</dt><dd>${selectedRequest.employerName}</dd></div>
          <div><dt>Broad area</dt><dd>${selectedRequest.serviceArea}</dd></div>
          <div><dt>Requested role</dt><dd>${selectedRequest.role}</dd></div>
          <div><dt>Quantity</dt><dd>${selectedRequest.count}</dd></div>
          <div><dt>Source</dt><dd>${selectedRequest.source}</dd></div>
          <div><dt>Coordinator note</dt><dd>${selectedRequest.coordinatorNote}</dd></div>
        </dl>
      </article>
      <article class="action-card">
        <h2>Presentation actions</h2>
        <p>Use these controls to move through the connected story without hunting for small links.</p>
        <div class="button-stack">
          <button type="button" class="primary-btn" data-action="record-follow-up">Show staff follow-up</button>
          <button type="button" class="secondary-btn" data-switch="intake">Add worker or employer</button>
          <button type="button" class="secondary-btn" data-switch="worker">Open worker request page</button>
          <button type="button" class="secondary-btn" data-switch="employer">Open employer status page</button>
          <button type="button" class="secondary-btn" data-switch="dashboard">Back to agency dashboard</button>
        </div>
      </article>
    </section>

    <section class="timeline" aria-label="Staff activity trail">
      <h2>Staff activity trail</h2>
      ${renderTimeline(state.workspace.timeline)}
    </section>
  `;
}

function renderWorkerMarkup(state, selectedRequest) {
  const requestPreview = state.workerInterestOpened
    ? `
      <section class="detail-panel inline-detail" aria-label="Worker interest request preview">
        <p class="eyebrow">Interest request preview</p>
        <h2>What the worker would review next</h2>
        <dl class="detail-list">
          <div><dt>Opportunity</dt><dd>${selectedRequest.role}</dd></div>
          <div><dt>Broad area</dt><dd>${selectedRequest.serviceArea}</dd></div>
          <div><dt>Schedule</dt><dd>${selectedRequest.serviceWindow}</dd></div>
          <div><dt>Agency next step</dt><dd>Coordinator contacts the worker for a human-reviewed conversation.</dd></div>
        </dl>
      </section>
    `
    : "";

  return `
    <section class="workspace-hero">
      <div>
        <p class="eyebrow">Worker-facing preview</p>
        <h2>${selectedRequest.role}</h2>
        <p>${selectedRequest.workerSafeSummary}</p>
      </div>
      <dl class="deadline-card">
        <div><dt>Area</dt><dd>${selectedRequest.serviceArea}</dd></div>
        <div><dt>Schedule</dt><dd>${selectedRequest.serviceWindow}</dd></div>
        <div><dt>Staff contact</dt><dd>Agency coordinator</dd></div>
      </dl>
    </section>
    <section class="action-card">
      <h2>Worker request action</h2>
      <p>This action opens a preview of the request handoff instead of pretending the worker was placed automatically.</p>
      <button type="button" class="primary-btn" data-action="open-worker-interest">${DEMO_DATA.worker.actionText}</button>
      <button type="button" class="secondary-btn" data-switch="workspace">Back to request detail</button>
    </section>
    ${requestPreview}
  `;
}

function renderEmployerMarkup(state, selectedRequest) {
  const updatePreview = state.employerUpdateOpened
    ? `
      <section class="detail-panel inline-detail" aria-label="Employer update preview">
        <p class="eyebrow">Employer-facing update draft</p>
        <h2>Next update visible to employer</h2>
        <p>Your request is in agency review. Next update is scheduled for ${selectedRequest.due}.</p>
        <p>No worker identity, exact address, or private contact information is exposed here.</p>
      </section>
    `
    : "";

  return `
    <section class="workspace-hero">
      <div>
        <p class="eyebrow">Employer-facing status</p>
        <h2>${selectedRequest.employerName}</h2>
        <p>${selectedRequest.employerVisibleStatus}: ${selectedRequest.summary}</p>
      </div>
      <dl class="deadline-card">
        <div><dt>Request</dt><dd>${selectedRequest.label}</dd></div>
        <div><dt>Service window</dt><dd>${selectedRequest.serviceWindow}</dd></div>
        <div><dt>Next update</dt><dd>${selectedRequest.due}</dd></div>
      </dl>
    </section>
    <section class="two-column" aria-label="Employer status sections">
      <article class="action-card">
        <h2>Visible milestone trail</h2>
        <ol class="timeline-list">
          ${DEMO_DATA.employerMilestones
            .map(
              (milestone, index) => `
                <li><span class="timeline-index">${index + 1}</span><span><strong>${milestone.when} — ${milestone.label}:</strong> ${milestone.note}</span></li>
              `,
            )
            .join("")}
        </ol>
      </article>
      <article class="action-card">
        <h2>Employer-safe request summary</h2>
        <dl class="detail-list">
          <div><dt>Status</dt><dd>${selectedRequest.employerVisibleStatus}</dd></div>
          <div><dt>Broad area</dt><dd>${selectedRequest.serviceArea}</dd></div>
          <div><dt>Coordinator-owned next step</dt><dd>${selectedRequest.nextStep}</dd></div>
        </dl>
        <div class="button-stack">
          <button type="button" class="primary-btn" data-action="open-employer-update">Open update preview</button>
          <button type="button" class="secondary-btn" data-switch="workspace">Back to request detail</button>
        </div>
      </article>
    </section>
    ${updatePreview}
  `;
}

function setActiveNav(currentViewId) {
  const navButtons = document.querySelectorAll("#demo-navigation [data-switch]");

  for (const button of navButtons) {
    const isCurrent = button.dataset.switch === currentViewId;
    button.classList.toggle("active", isCurrent);
    if (isCurrent) {
      button.setAttribute("aria-current", "page");
    } else {
      button.removeAttribute("aria-current");
    }
  }
}

function announceStatus(message) {
  const statusRegion = document.getElementById("demo-status-region");
  if (statusRegion) statusRegion.textContent = message;
}

function updateDocumentTitle(viewId) {
  document.title = `${VIEWS[viewId].pageTitle} — Golden Rose synthetic preview`;
}

function handleDemoInteraction(state, target) {
  const actionElement = target.closest("[data-action], [data-switch], [data-select-request]");
  if (!actionElement || actionElement.disabled) return false;

  const selectedRequestId = actionElement.dataset.selectRequest;
  if (selectedRequestId) Object.assign(state, selectRequest(state, selectedRequestId));

  const action = actionElement.dataset.action;
  if (action === "record-follow-up") {
    Object.assign(state, recordFictionalFollowUp(state));
    renderDemoApp(state);
    return true;
  }
  if (action === "open-worker-interest") {
    Object.assign(state, openWorkerInterest(state));
    renderDemoApp(state);
    return true;
  }
  if (action === "open-employer-update") {
    Object.assign(state, openEmployerUpdate(state));
    renderDemoApp(state);
    return true;
  }
  if (action === "add-employer-record") {
    Object.assign(state, addSyntheticIntakeRecord(state, "employer"));
    renderDemoApp(state);
    return true;
  }
  if (action === "add-worker-record") {
    Object.assign(state, addSyntheticIntakeRecord(state, "worker"));
    renderDemoApp(state);
    return true;
  }

  const nextViewId = actionElement.dataset.switch;
  if (DEMO_VIEW_SEQUENCE.includes(nextViewId)) {
    state.activeView = nextViewId;
    renderDemoApp(state);
    return true;
  }

  return false;
}

function wireDemoEvents(state) {
  const root = document.getElementById("demo-root");
  const nav = document.getElementById("demo-navigation");

  root?.addEventListener("click", (event) => {
    handleDemoInteraction(state, event.target);
  });

  nav?.addEventListener("click", (event) => {
    handleDemoInteraction(state, event.target);
  });
}

function renderDemoContainer(state) {
  const view = renderViewMarkup(state, state.activeView);

  return `
    <h1 id="demo-view-heading" tabindex="-1">${view.viewTitle}</h1>
    <div class="screen-content">
      ${view.content}
    </div>
  `;
}

export function renderDemoApp(state) {
  const resolvedState = {
    ...state,
    activeView: ensureValidViewId(state.activeView),
    selectedRequestId: getRequestById(state.selectedRequestId).id,
    intakeRecords: state.intakeRecords ?? [],
    workspace: state.workspace,
  };

  Object.assign(state, resolvedState);

  const root = document.getElementById("demo-root");
  if (!root) return;

  root.innerHTML = renderDemoContainer(resolvedState);
  root.querySelector("#demo-view-heading")?.focus();

  const currentView = resolvedState.activeView;
  const selectedRequest = getRequestById(resolvedState.selectedRequestId);
  const statusText = resolvedState.workspace.confirmationMessage
    ? `${resolvedState.workspace.confirmationMessage}`
    : `${VIEWS[currentView].navLabel} showing ${selectedRequest.label}.`;
  announceStatus(statusText);
  setActiveNav(currentView);
  updateDocumentTitle(currentView);
}

function bootstrapDemoApp() {
  const root = document.getElementById("demo-root");
  if (!root) return;

  const state = createInitialDemoState();
  wireDemoEvents(state);
  renderDemoApp(state);
}

if (typeof window !== "undefined" && typeof document !== "undefined") {
  if (document.readyState === "loading") {
    window.addEventListener("DOMContentLoaded", bootstrapDemoApp);
  } else {
    bootstrapDemoApp();
  }
}
