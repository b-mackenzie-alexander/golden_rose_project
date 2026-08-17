export const DEMO_NOTICE =
  "Concept demonstration — fictional synthetic data — local presentation only.";

export const LOCALES = Object.freeze({
  en: "en",
  es: "es",
});

const DEFAULT_LOCALE = LOCALES.en;

export const VIEWS = Object.freeze({
  dashboard: Object.freeze({
    id: "dashboard",
    navLabel: Object.freeze({ en: "Agency dashboard", es: "Panel operativo" }),
    pageTitle: Object.freeze({
      en: "Agency operations dashboard",
      es: "Panel operativo de la agencia",
    }),
  }),
  workspace: Object.freeze({
    id: "workspace",
    navLabel: Object.freeze({ en: "Request detail", es: "Detalle de solicitud" }),
    pageTitle: Object.freeze({
      en: "Request detail and staff coordination",
      es: "Detalle de solicitud y coordinación del personal",
    }),
  }),
  intake: Object.freeze({
    id: "intake",
    navLabel: Object.freeze({ en: "Add records", es: "Registrar fichas" }),
    pageTitle: Object.freeze({
      en: "Manual worker and employer intake",
      es: "Registro manual de trabajadores y empleadores",
    }),
  }),
  worker: Object.freeze({
    id: "worker",
    navLabel: Object.freeze({ en: "Worker view", es: "Vista del trabajador" }),
    pageTitle: Object.freeze({
      en: "Worker opportunity view",
      es: "Vista de oportunidad laboral",
    }),
  }),
  employer: Object.freeze({
    id: "employer",
    navLabel: Object.freeze({ en: "Employer view", es: "Vista del cliente" }),
    pageTitle: Object.freeze({
      en: "Employer request status view",
      es: "Vista del estado de la solicitud del cliente",
    }),
  }),
});

const DEMO_VIEW_SEQUENCE = Object.freeze([
  VIEWS.dashboard.id,
  VIEWS.workspace.id,
  VIEWS.intake.id,
  VIEWS.worker.id,
  VIEWS.employer.id,
]);

const TRANSLATIONS = Object.freeze({
  en: Object.freeze({
    notice: DEMO_NOTICE,
    navAriaLabel: "Demo views",
    navDescription: "Stakeholder walkthrough: agency workflow, worker view, and employer view.",
    skipLink: "Skip to main content",
    languageLabel: "Language",
    englishLabel: "English",
    spanishLabel: "Español",
    statusShowing: "showing",
    metricsAria: "Agency workflow metrics",
    metrics: Object.freeze([
      Object.freeze({ value: "5", label: "open employer requests" }),
      Object.freeze({ value: "14:30", label: "next staff deadline" }),
      Object.freeze({ value: "2", label: "full-time searches still open" }),
      Object.freeze({ value: "2", label: "paper records ready to enter" }),
    ]),
    requestCardsAria: "Actionable request cards",
    myWorkTodayHeading: "My work today",
    myWorkTodayAria: "My work today panel",
    activeRequestsHeading: "Today's scheduled requests",
    openSearchesHeading: "Open searches",
    openSearchesDescription: "Longer-running employer requests that stay visible until the search is closed.",
    openRequestLabel: "Open request",
    workTodayItems: Object.freeze([
      "2 follow-ups due before 15:00",
      "1 new worker packet ready for review",
      "1 employer request waiting on scope confirmation",
      "2 open full-time searches still need weekly follow-up",
    ]),
    selectedRequestEyebrow: "Selected request",
    requestOverviewAction: "Open request overview",
    fullRequestDetail: "Open full request detail",
    addWorkerOrEmployer: "Add worker or employer",
    previewWorkerView: "Preview worker view",
    previewEmployerView: "Preview employer view",
    requestDetailAria: "Selected request quick detail",
    employerLabel: "Employer",
    broadAreaLabel: "Broad area",
    dueLabel: "Due",
    statusLabel: "Status",
    nextStaffStepLabel: "Next staff step",
    assignedToLabel: "Assigned to",
    lastUpdatedLabel: "Last updated",
    roleLabel: "Role",
    windowLabel: "Window",
    ownerLabel: "Owner",
    sourceLabel: "Source",
    quantityLabel: "Quantity",
    coordinatorLabel: "Coordinator",
    coordinatorNoteLabel: "Coordinator note",
    requestedRoleLabel: "Requested role",
    serviceWindowLabel: "Service window",
    requestLabel: "Request",
    nextUpdateLabel: "Next update",
    coordinatorOwnedNextStepLabel: "Coordinator-owned next step",
    continuityLabel: "Continuity",
    capturedByLabel: "Captured by",
    reviewStateLabel: "Review state",
    nameLabel: "Name",
    areaLabel: "Area",
    scheduleLabel: "Schedule",
    staffContactLabel: "Staff contact",
    opportunityLabel: "Opportunity",
    agencyNextStepLabel: "Agency next step",
    currentPaperBacklogLabel: "Current paper backlog",
    continuityShownLabel: "Continuity shown",
    liveDatabaseLabel: "Live database",
    dashboardContentAria: "Agency dashboard content",
    requestDetailSectionsAria: "Request detail sections",
    manualIntakeActionsAria: "Manual intake actions",
    queuePreviewAria: "Shared staff queue preview",
    workerPreviewAria: "Worker interest request preview",
    employerSectionsAria: "Employer status sections",
    employerUpdateAria: "Employer update preview",
    timelineAria: "Staff activity trail",
    firstRolloutWorkflow: "First rollout workflow",
    manualRecordIntake: "Manual record intake",
    manualRecordIntro:
      "Staff can turn paper employer sheets and worker registration packets into shared draft records without needing a finished public portal.",
    currentPaperBacklogValue: "2 starter records",
    continuityShownValue: "Shared staff queue concept",
    liveDatabaseValue: "Not connected in this demo",
    addEmployerFromPaper: "Add employer from paper",
    addEmployerDescription:
      "Use a synthetic paper-intake example to create an employer draft that another staff member could continue reviewing.",
    addEmployerDraft: "Add synthetic employer draft",
    addWorkerFromPacket: "Add worker from packet",
    addWorkerDescription:
      "Use a synthetic walk-in packet to create a worker draft that stays agency-reviewed before any outreach.",
    addWorkerDraft: "Add synthetic worker draft",
    queuePreviewHeading: "Shared staff queue preview",
    noSyntheticRecords:
      "No synthetic records have been added yet. Use the intake actions to show how paper records become shared staff-visible drafts.",
    employerDraftEyebrow: "Employer draft",
    workerDraftEyebrow: "Worker draft",
    backToDashboard: "Back to agency dashboard",
    openRequestDetail: "Open request detail",
    agencyOwnedRequestDetail: "Agency-owned request detail",
    staffCoordinationDetail: "Staff coordination detail",
    presentationActions: "Presentation actions",
    presentationActionsDescription:
      "Use these controls to move through the connected story without hunting for small links.",
    assignToMe: "Assign to me",
    markReviewComplete: "Mark review complete",
    setWaitingOnEmployer: "Waiting on employer",
    prepareWorkerOutreach: "Prepare worker outreach",
    showStaffFollowUp: "Show staff follow-up",
    openWorkerRequestPage: "Open worker request page",
    openEmployerStatusPage: "Open employer status page",
    backToRequestDetail: "Back to request detail",
    staffActivityTrail: "Staff activity trail",
    workerFacingPreview: "Worker-facing preview",
    workerRequestAction: "Worker request action",
    workerRequestActionDescription:
      "This action opens a preview of the request handoff instead of pretending the worker was placed automatically.",
    workerInterestAction: "Open interest request",
    interestRequestPreview: "Interest request preview",
    workerWouldReviewNext: "What the worker would review next",
    agencyNextStepValue: "Coordinator contacts the worker for a human-reviewed conversation.",
    employerFacingStatus: "Employer-facing status",
    visibleMilestoneTrail: "Visible milestone trail",
    employerSafeRequestSummary: "Employer-safe request summary",
    employerUpdateDraft: "Employer-facing update draft",
    nextUpdateVisible: "Next update visible to employer",
    updatePreviewAction: "Open update preview",
    employerUpdateBodyPrefix: "Your request is in agency review. Next update is scheduled for",
    employerUpdateBodySuffix: ".",
    employerPrivacyNote:
      "No worker identity, exact address, or private contact information is exposed here.",
    confirmationAlreadyShown:
      "Follow-up is already shown in this presentation run; refresh resets the synthetic state.",
    timelineCurrentRunPrefix: "Current run — staff follow-up displayed for",
    timelineCurrentRunBefore: "before",
    employerDraftAdded: "Employer draft added to the shared staff queue.",
    workerDraftAdded: "Worker draft added to the shared staff queue.",
    draftAlreadyInQueue: "draft is already in the shared staff queue for this presentation run.",
    timelineDraftEnteredPrefix: "Current run —",
    timelineDraftEnteredMiddle: "draft entered from",
    sharedQueue: "shared staff queue",
    anotherWorkstation: "another workstation",
    languageChanged: "Language changed to English.",
    workflowStateReviewComplete: "Reviewed — ready for worker outreach",
    workflowStateWaitingOnEmployer: "Waiting on employer clarification",
    workflowStateWorkerOutreach: "Worker outreach in progress",
    workflowNextReviewComplete: "Open the worker preview and queue outreach today.",
    workflowNextWaitingOnEmployer: "Hold worker outreach until the employer confirms the missing detail.",
    workflowNextWorkerOutreach: "Use the worker preview to explain the opportunity and collect interest.",
    workflowHistoryAssigned: "assigned to Marisol R. for next action",
    workflowHistoryReviewComplete: "marked reviewed and ready for worker outreach",
    workflowHistoryWaitingOnEmployer: "moved to waiting on employer clarification",
    workflowHistoryWorkerOutreach: "moved into worker outreach preparation",
    localeDocumentTitleSuffix: "Golden Rose synthetic preview",
    today: "Today",
    tomorrow: "Tomorrow",
    high: "High",
    medium: "Medium",
    routine: "Routine",
    timelineEntries: Object.freeze([
      "09:12 — Employer request received and triaged into staff review.",
      "09:34 — Coordinator added service-window notes and broad area only.",
      "10:03 — Second request grouped under the same employer workspace.",
      "10:28 — Worker-safe summary drafted for the same-day request.",
    ]),
  }),
  es: Object.freeze({
    notice: "Demostración conceptual — datos sintéticos ficticios — solo para presentación local.",
    navAriaLabel: "Vistas de la demostración",
    navDescription:
      "Recorrido para la presentación: flujo de la agencia, vista del trabajador y vista del cliente.",
    skipLink: "Saltar al contenido principal",
    languageLabel: "Idioma",
    englishLabel: "English",
    spanishLabel: "Español",
    statusShowing: "mostrando",
    metricsAria: "Métricas del flujo de trabajo de la agencia",
    metrics: Object.freeze([
      Object.freeze({ value: "5", label: "solicitudes abiertas de empleadores" }),
      Object.freeze({ value: "14:30", label: "próximo plazo del personal" }),
      Object.freeze({ value: "2", label: "búsquedas de tiempo completo aún abiertas" }),
      Object.freeze({ value: "2", label: "registros en papel listos para capturar" }),
    ]),
    requestCardsAria: "Tarjetas de solicitudes con acción",
    myWorkTodayHeading: "Mi trabajo de hoy",
    myWorkTodayAria: "Panel de trabajo de hoy",
    activeRequestsHeading: "Solicitudes programadas de hoy",
    openSearchesHeading: "Búsquedas abiertas",
    openSearchesDescription: "Solicitudes de empleadores de más largo plazo que siguen visibles hasta que la búsqueda se cierre.",
    openRequestLabel: "Solicitud abierta",
    workTodayItems: Object.freeze([
      "2 seguimientos pendientes antes de las 15:00",
      "1 formulario nuevo de trabajador listo para revisión",
      "1 solicitud de empleador en espera de confirmar alcance",
      "2 búsquedas abiertas de tiempo completo aún necesitan seguimiento semanal",
    ]),
    selectedRequestEyebrow: "Solicitud seleccionada",
    requestOverviewAction: "Abrir resumen de solicitud",
    fullRequestDetail: "Abrir detalle completo de la solicitud",
    addWorkerOrEmployer: "Agregar trabajador o empleador",
    previewWorkerView: "Vista previa del trabajador",
    previewEmployerView: "Vista previa del empleador",
    requestDetailAria: "Detalle rápido de la solicitud seleccionada",
    employerLabel: "Empleador",
    broadAreaLabel: "Zona general",
    dueLabel: "Vence",
    statusLabel: "Estado",
    nextStaffStepLabel: "Próximo paso del equipo",
    assignedToLabel: "Asignado a",
    lastUpdatedLabel: "Última actualización",
    roleLabel: "Rol",
    windowLabel: "Horario",
    ownerLabel: "Responsable",
    sourceLabel: "Origen",
    quantityLabel: "Cantidad",
    coordinatorLabel: "Coordinador",
    coordinatorNoteLabel: "Nota del coordinador",
    requestedRoleLabel: "Rol solicitado",
    serviceWindowLabel: "Horario de servicio",
    requestLabel: "Solicitud",
    nextUpdateLabel: "Próxima actualización",
    coordinatorOwnedNextStepLabel: "Próximo paso del coordinador",
    continuityLabel: "Continuidad",
    capturedByLabel: "Registrado por",
    reviewStateLabel: "Estado de revisión",
    nameLabel: "Nombre",
    areaLabel: "Área",
    scheduleLabel: "Horario",
    staffContactLabel: "Contacto del personal",
    opportunityLabel: "Oportunidad",
    agencyNextStepLabel: "Próximo paso de la agencia",
    currentPaperBacklogLabel: "Volumen actual en papel",
    continuityShownLabel: "Continuidad demostrada",
    liveDatabaseLabel: "Base de datos en vivo",
    dashboardContentAria: "Contenido del panel de agencia",
    requestDetailSectionsAria: "Secciones del detalle de la solicitud",
    manualIntakeActionsAria: "Acciones de ingreso manual",
    queuePreviewAria: "Vista previa de la cola compartida del personal",
    workerPreviewAria: "Vista previa de solicitud de interés",
    employerSectionsAria: "Secciones del estado del cliente",
    employerUpdateAria: "Vista previa de actualización para el empleador",
    timelineAria: "Historial de actividad del equipo",
    firstRolloutWorkflow: "Flujo del primer despliegue",
    manualRecordIntake: "Registro manual de fichas",
    manualRecordIntro:
      "El equipo puede convertir formularios en papel de empleadores y registros de trabajadores en borradores compartidos sin depender de un portal público terminado.",
    currentPaperBacklogValue: "2 registros iniciales",
    continuityShownValue: "Concepto de cola compartida del personal",
    liveDatabaseValue: "Sin conexión en esta demostración",
    addEmployerFromPaper: "Agregar empleador desde papel",
    addEmployerDescription:
      "Use un ejemplo sintético de ficha en papel para crear un borrador de empleador que otro miembro del equipo pueda seguir revisando.",
    addEmployerDraft: "Agregar borrador sintético de empleador",
    addWorkerFromPacket: "Agregar trabajador desde formulario",
    addWorkerDescription:
      "Use un formulario sintético de registro presencial para crear un borrador de trabajador que siga bajo revisión de la agencia antes de cualquier contacto.",
    addWorkerDraft: "Agregar borrador sintético de trabajador",
    queuePreviewHeading: "Vista previa de la cola compartida del equipo",
    noSyntheticRecords:
      "Todavía no se han agregado registros sintéticos. Use estas acciones para mostrar cómo los registros en papel se convierten en borradores visibles para el equipo.",
    employerDraftEyebrow: "Borrador de empleador",
    workerDraftEyebrow: "Borrador de trabajador",
    backToDashboard: "Volver al panel de agencia",
    openRequestDetail: "Abrir detalle de solicitud",
    agencyOwnedRequestDetail: "Detalle de la solicitud gestionado por la agencia",
    staffCoordinationDetail: "Detalle de coordinación del equipo",
    presentationActions: "Acciones de la presentación",
    presentationActionsDescription:
      "Use estos controles para recorrer la historia conectada sin depender de enlaces pequeños o difíciles de encontrar.",
    assignToMe: "Asignarme esta solicitud",
    markReviewComplete: "Marcar revisión completa",
    setWaitingOnEmployer: "Poner en espera por el cliente",
    prepareWorkerOutreach: "Preparar contacto con trabajadores",
    showStaffFollowUp: "Mostrar seguimiento del equipo",
    openWorkerRequestPage: "Abrir página de solicitud del trabajador",
    openEmployerStatusPage: "Abrir página de estado del empleador",
    backToRequestDetail: "Volver al detalle de solicitud",
    staffActivityTrail: "Historial de actividad del equipo",
    workerFacingPreview: "Vista del trabajador",
    workerRequestAction: "Acción del trabajador",
    workerRequestActionDescription:
      "Esta acción abre una vista previa del siguiente paso para el trabajador sin fingir que hubo una asignación automática.",
    workerInterestAction: "Abrir solicitud de interés",
    interestRequestPreview: "Vista previa de solicitud de interés",
    workerWouldReviewNext: "Lo que vería el trabajador a continuación",
    agencyNextStepValue: "La agencia contacta al trabajador para una conversación revisada por una persona.",
    employerFacingStatus: "Estado para el cliente",
    visibleMilestoneTrail: "Cronología visible",
    employerSafeRequestSummary: "Resumen visible para el cliente",
    employerUpdateDraft: "Borrador de actualización para el empleador",
    nextUpdateVisible: "Próxima actualización para el cliente",
    updatePreviewAction: "Abrir vista previa de actualización",
    employerUpdateBodyPrefix: "Su solicitud está en revisión de la agencia. La próxima actualización está programada para",
    employerUpdateBodySuffix: ".",
    employerPrivacyNote:
      "Aquí no se muestran la identidad del trabajador, la dirección exacta ni información privada de contacto.",
    confirmationAlreadyShown:
      "El seguimiento ya se muestra en esta ejecución de la presentación; actualizar reinicia el estado sintético.",
    timelineCurrentRunPrefix: "Ejecución actual — seguimiento del personal mostrado para",
    timelineCurrentRunBefore: "antes de",
    employerDraftAdded: "Borrador de empleador agregado a la cola compartida del personal.",
    workerDraftAdded: "Borrador de trabajador agregado a la cola compartida del personal.",
    draftAlreadyInQueue: "ya está en la cola compartida del personal para esta ejecución de la presentación.",
    timelineDraftEnteredPrefix: "Ejecución actual —",
    timelineDraftEnteredMiddle: "borrador ingresado desde",
    sharedQueue: "cola compartida del personal",
    anotherWorkstation: "otro equipo de trabajo",
    languageChanged: "Idioma cambiado a Español.",
    workflowStateReviewComplete: "Revisada — lista para contacto con trabajadores",
    workflowStateWaitingOnEmployer: "En espera de aclaración del cliente",
    workflowStateWorkerOutreach: "Contacto con trabajadores en preparación",
    workflowNextReviewComplete: "Abrir la vista del trabajador y dejar listo el contacto de hoy.",
    workflowNextWaitingOnEmployer: "Pausar el contacto con trabajadores hasta que el cliente confirme el dato pendiente.",
    workflowNextWorkerOutreach: "Usar la vista del trabajador para explicar la oportunidad y registrar interés.",
    workflowHistoryAssigned: "asignada a Marisol R. para la próxima acción",
    workflowHistoryReviewComplete: "marcada como revisada y lista para contacto con trabajadores",
    workflowHistoryWaitingOnEmployer: "movida a espera por aclaración del cliente",
    workflowHistoryWorkerOutreach: "movida a preparación de contacto con trabajadores",
    localeDocumentTitleSuffix: "vista previa sintética de Golden Rose",
    today: "Hoy",
    tomorrow: "Mañana",
    high: "Alta",
    medium: "Media",
    routine: "Rutinaria",
    timelineEntries: Object.freeze([
      "09:12 — Se recibió la solicitud del empleador y se envió a revisión del equipo.",
      "09:34 — La coordinadora agregó notas sobre el horario de servicio y solo la zona general.",
      "10:03 — La segunda solicitud se agrupó en el mismo espacio de trabajo del empleador.",
      "10:28 — Se preparó un resumen apto para trabajadores para la solicitud del mismo día.",
    ]),
  }),
});

const DEMO_EVENTS = Object.freeze([
  Object.freeze({
    id: "req-harbor-cleaning",
    label: Object.freeze({
      en: "Same-day coverage request",
      es: "Solicitud de cobertura para el mismo día",
    }),
    status: Object.freeze({
      en: "Needs staff review",
      es: "Necesita revisión del personal",
    }),
    owner: "Priya K.",
    employerName: "Harbor & Pine Hospitality",
    serviceArea: Object.freeze({
      en: "Downtown service area",
      es: "Área de servicio del centro",
    }),
    due: Object.freeze({ en: "Today 14:30", es: "Hoy 14:30" }),
    deadlineDisplay: Object.freeze({ en: "Due Today 14:30", es: "Vence Hoy 14:30" }),
    dueMode: "scheduled",
    serviceWindow: Object.freeze({ en: "Fri 17:00-21:00", es: "Vie 17:00-21:00" }),
    lastUpdated: "10:28",
    role: Object.freeze({ en: "General Cleaner", es: "Personal general de limpieza" }),
    count: 2,
    urgency: Object.freeze({ en: "High", es: "Alta" }),
    source: Object.freeze({
      en: "Employer message at 09:12",
      es: "Mensaje del empleador a las 09:12",
    }),
    summary: Object.freeze({
      en: "Two evening cleaning staff requested for a banquet reset window after a late event update.",
      es: "Se solicitaron dos personas para limpieza nocturna durante una ventana de reorganización después de una actualización tardía del evento.",
    }),
    nextStep: Object.freeze({
      en: "Confirm scope, prepare worker-safe summary, and schedule outreach before 14:30.",
      es: "Confirmar el alcance, preparar un resumen apto para trabajadores y programar el contacto antes de las 14:30.",
    }),
    coordinatorNote: Object.freeze({
      en: "Employer can accept staggered arrivals if the agency confirms the first person by 15:30.",
      es: "El empleador puede aceptar llegadas escalonadas si la agencia confirma a la primera persona antes de las 15:30.",
    }),
    workerSafeSummary: Object.freeze({
      en: "Evening cleaning support in the downtown service area. Tasks include room reset, supply restock, and light closing support.",
      es: "Apoyo de limpieza nocturna en el área de servicio del centro. Las tareas incluyen reorganizar salas, reponer suministros y apoyo ligero al cierre.",
    }),
    employerVisibleStatus: Object.freeze({
      en: "Agency reviewing coverage options",
      es: "La agencia está revisando opciones de cobertura",
    }),
  }),
  Object.freeze({
    id: "req-pine-event-setup",
    label: Object.freeze({ en: "Event setup support", es: "Apoyo para montaje de evento" }),
    status: Object.freeze({ en: "Coverage in progress", es: "Cobertura en progreso" }),
    owner: "Marisol R.",
    employerName: "Harbor & Pine Hospitality",
    serviceArea: Object.freeze({ en: "Central service area", es: "Área de servicio central" }),
    due: Object.freeze({ en: "Today 16:00", es: "Hoy 16:00" }),
    deadlineDisplay: Object.freeze({ en: "Due Today 16:00", es: "Vence Hoy 16:00" }),
    dueMode: "scheduled",
    serviceWindow: Object.freeze({ en: "Sat 10:00-14:00", es: "Sáb 10:00-14:00" }),
    lastUpdated: "10:21",
    role: Object.freeze({ en: "Back-of-house Support", es: "Apoyo de logística interna" }),
    count: 1,
    urgency: Object.freeze({ en: "Medium", es: "Media" }),
    source: Object.freeze({ en: "Phone intake at 10:03", es: "Ingreso por teléfono a las 10:03" }),
    summary: Object.freeze({
      en: "One back-of-house support worker requested for staging, supply movement, and event room turnover.",
      es: "Se solicitó una persona de apoyo interno para montaje, movimiento de suministros y reorganización del salón del evento.",
    }),
    nextStep: Object.freeze({
      en: "Confirm physical requirements and prepare the employer-facing status update.",
      es: "Confirmar requisitos físicos y preparar la actualización visible para el empleador.",
    }),
    coordinatorNote: Object.freeze({
      en: "Ask employer to confirm whether supply carts are available before final outreach.",
      es: "Pedir al empleador que confirme si hay carritos de suministros disponibles antes del contacto final.",
    }),
    workerSafeSummary: Object.freeze({
      en: "Short Saturday setup support in the central service area with staging and room-turnover tasks.",
      es: "Apoyo breve de montaje el sábado en el área de servicio central con tareas de preparación y reorganización de salas.",
    }),
    employerVisibleStatus: Object.freeze({
      en: "Details being confirmed",
      es: "Se están confirmando los detalles",
    }),
  }),
  Object.freeze({
    id: "req-harbor-followup",
    label: Object.freeze({ en: "Employer follow-up due", es: "Seguimiento con el empleador pendiente" }),
    status: Object.freeze({ en: "Awaiting update", es: "En espera de actualización" }),
    owner: "Priya K.",
    employerName: "Harbor & Pine Hospitality",
    serviceArea: Object.freeze({ en: "Downtown service area", es: "Área de servicio del centro" }),
    due: Object.freeze({ en: "Tomorrow 09:30", es: "Mañana 09:30" }),
    deadlineDisplay: Object.freeze({ en: "Due Tomorrow 09:30", es: "Vence Mañana 09:30" }),
    dueMode: "scheduled",
    serviceWindow: Object.freeze({
      en: "Next week schedule review",
      es: "Revisión del calendario de la próxima semana",
    }),
    lastUpdated: "09:48",
    role: Object.freeze({ en: "Recurring cleaning support", es: "Apoyo recurrente de limpieza" }),
    count: 3,
    urgency: Object.freeze({ en: "Routine", es: "Rutinaria" }),
    source: Object.freeze({ en: "Standing account cadence", es: "Cadencia habitual de la cuenta" }),
    summary: Object.freeze({
      en: "Recurring support forecast needs a staff check-in before the next weekly request cycle.",
      es: "La previsión de apoyo recurrente necesita una revisión del personal antes del próximo ciclo semanal de solicitudes.",
    }),
    nextStep: Object.freeze({
      en: "Confirm forecasted dates and update the employer status trail.",
      es: "Confirmar fechas previstas y actualizar el historial de estado para el empleador.",
    }),
    coordinatorNote: Object.freeze({
      en: "Keep this as a planning conversation; do not expose worker identities in the employer view.",
      es: "Mantener esto como una conversación de planificación; no exponer identidades de trabajadores en la vista del empleador.",
    }),
    workerSafeSummary: Object.freeze({
      en: "Recurring support forecast; details are not ready for worker-facing outreach yet.",
      es: "Previsión de apoyo recurrente; los detalles todavía no están listos para contacto con trabajadores.",
    }),
    employerVisibleStatus: Object.freeze({ en: "Follow-up scheduled", es: "Seguimiento programado" }),
  }),
  Object.freeze({
    id: "req-rivera-admin",
    label: Object.freeze({ en: "Full-time office administrator search", es: "Búsqueda de administradora de oficina a tiempo completo" }),
    status: Object.freeze({ en: "Open search", es: "Búsqueda abierta" }),
    owner: "Marisol R.",
    employerName: "Rivera Home Services",
    serviceArea: Object.freeze({ en: "North service area", es: "Área de servicio norte" }),
    due: Object.freeze({ en: "Open until filled", es: "Abierta hasta cubrirse" }),
    deadlineDisplay: Object.freeze({ en: "Open until filled", es: "Abierta hasta cubrirse" }),
    dueMode: "open",
    serviceWindow: Object.freeze({ en: "Full-time weekday placement", es: "Colocación fija de lunes a viernes" }),
    lastUpdated: "11:02",
    role: Object.freeze({ en: "Office Administrator", es: "Administradora de oficina" }),
    count: 1,
    urgency: Object.freeze({ en: "Routine", es: "Rutinaria" }),
    source: Object.freeze({ en: "Employer follow-up call at 11:02", es: "Llamada de seguimiento del empleador a las 11:02" }),
    summary: Object.freeze({
      en: "Employer wants a full-time office administrator and expects the search to remain active until the right long-term fit is found.",
      es: "El empleador busca una administradora de oficina a tiempo completo y espera mantener la búsqueda activa hasta encontrar una opción estable.",
    }),
    nextStep: Object.freeze({
      en: "Keep this request visible in the open queue and review candidate pipeline notes during weekly follow-up.",
      es: "Mantener esta solicitud visible en la cola abierta y revisar las notas de candidaturas durante el seguimiento semanal.",
    }),
    coordinatorNote: Object.freeze({
      en: "No close date; keep it on the dashboard until the employer confirms the search is complete.",
      es: "No tiene fecha de cierre; debe permanecer en el panel hasta que el empleador confirme que la búsqueda terminó.",
    }),
    workerSafeSummary: Object.freeze({
      en: "Full-time office administration opportunity with weekday hours and agency-led follow-up.",
      es: "Oportunidad de administración de oficina a tiempo completo con horario entre semana y seguimiento dirigido por la agencia.",
    }),
    employerVisibleStatus: Object.freeze({ en: "Longer-term search remains open", es: "La búsqueda de largo plazo sigue abierta" }),
  }),
  Object.freeze({
    id: "req-eastside-cook",
    label: Object.freeze({ en: "Full-time cook placement search", es: "Búsqueda de cocinero fijo a tiempo completo" }),
    status: Object.freeze({ en: "Open search", es: "Búsqueda abierta" }),
    owner: "Priya K.",
    employerName: "Eastside Family Dining",
    serviceArea: Object.freeze({ en: "East service area", es: "Área de servicio este" }),
    due: Object.freeze({ en: "Open until filled", es: "Abierta hasta cubrirse" }),
    deadlineDisplay: Object.freeze({ en: "Open until filled", es: "Abierta hasta cubrirse" }),
    dueMode: "open",
    serviceWindow: Object.freeze({ en: "Full-time kitchen schedule", es: "Horario fijo de cocina" }),
    lastUpdated: "10:42",
    role: Object.freeze({ en: "Line Cook", es: "Cocinero de línea" }),
    count: 2,
    urgency: Object.freeze({ en: "Routine", es: "Rutinaria" }),
    source: Object.freeze({ en: "Standing employer request", es: "Solicitud activa del empleador" }),
    summary: Object.freeze({
      en: "Employer is looking for two full-time kitchen workers and wants the request kept active until both positions are filled.",
      es: "El empleador busca dos trabajadores de cocina a tiempo completo y quiere mantener la solicitud activa hasta cubrir ambas posiciones.",
    }),
    nextStep: Object.freeze({
      en: "Keep weekly outreach moving and surface this search in the team's daily priorities until it closes.",
      es: "Mantener el contacto semanal activo y dejar esta búsqueda visible en las prioridades diarias del equipo hasta su cierre.",
    }),
    coordinatorNote: Object.freeze({
      en: "Do not let this fall out of view just because it is not tied to a same-day fill date.",
      es: "No dejar que esta solicitud desaparezca de la vista solo porque no tiene una fecha inmediata de cobertura.",
    }),
    workerSafeSummary: Object.freeze({
      en: "Full-time kitchen opportunity with stable weekday scheduling and agency review.",
      es: "Oportunidad fija de cocina a tiempo completo con horario estable y revisión de la agencia.",
    }),
    employerVisibleStatus: Object.freeze({ en: "Full-time search remains open", es: "La búsqueda fija sigue abierta" }),
  }),
]);

const EMPLOYER_MILESTONES = Object.freeze([
  Object.freeze({
    label: Object.freeze({ en: "Request received", es: "Solicitud recibida" }),
    when: "09:12",
    note: Object.freeze({
      en: "Agency has the staffing request.",
      es: "La agencia ya tiene la solicitud de personal.",
    }),
  }),
  Object.freeze({
    label: Object.freeze({ en: "Scope review", es: "Revisión de alcance" }),
    when: "10:28",
    note: Object.freeze({
      en: "Service window and task summary are being checked.",
      es: "Se están revisando el horario de servicio y el resumen de tareas.",
    }),
  }),
  Object.freeze({
    label: Object.freeze({ en: "Coordinator outreach", es: "Contacto del coordinador" }),
    when: "14:30",
    note: Object.freeze({
      en: "Next visible update is scheduled for this afternoon.",
      es: "La próxima actualización visible está programada para esta tarde.",
    }),
  }),
]);

const INTAKE_TEMPLATES = Object.freeze({
  employer: Object.freeze({
    id: "employer-draft-harbor-annex",
    type: Object.freeze({ en: "Employer", es: "Empleador" }),
    name: "Harbor Annex Events",
    source: Object.freeze({ en: "Paper intake sheet", es: "Formulario de ingreso en papel" }),
    capturedBy: Object.freeze({ en: "Front desk staff", es: "Personal de recepción" }),
    status: Object.freeze({
      en: "Draft saved for staff review",
      es: "Borrador guardado para revisión del personal",
    }),
    continuityNote: Object.freeze({
      en: "Visible in the shared staff queue after entry.",
      es: "Visible en la cola compartida del personal después del ingreso.",
    }),
  }),
  worker: Object.freeze({
    id: "worker-draft-camila-r",
    type: Object.freeze({ en: "Worker", es: "Trabajador" }),
    name: "Camila R.",
    source: Object.freeze({ en: "Walk-in registration packet", es: "Paquete de registro presencial" }),
    capturedBy: Object.freeze({ en: "Front desk staff", es: "Personal de recepción" }),
    status: Object.freeze({
      en: "Draft saved for staff review",
      es: "Borrador guardado para revisión del personal",
    }),
    continuityNote: Object.freeze({
      en: "Available for agency follow-up from another workstation.",
      es: "Disponible para seguimiento de la agencia desde otro equipo de trabajo.",
    }),
  }),
});

export const DEMO_DATA = Object.freeze({
  employerName: "Harbor & Pine Hospitality",
  requestedBy: "Harbor Team",
  owner: "Priya K.",
  requestStatus: Object.freeze({ en: "Needs staff review", es: "Necesita revisión del personal" }),
  serviceArea: Object.freeze({ en: "Downtown service area", es: "Área de servicio del centro" }),
  worker: Object.freeze({
    displayName: "Jordan R.",
    preferredShift: Object.freeze({ en: "Day shift", es: "Turno diurno" }),
    actionText: Object.freeze({ en: "Open interest request", es: "Abrir solicitud de interés" }),
  }),
  requests: DEMO_EVENTS,
  employerMilestones: EMPLOYER_MILESTONES,
  intakeTemplates: INTAKE_TEMPLATES,
});

const FORBIDDEN_DECISION_TERMS = ["matched", "recommended", "eligible", "hire"];

function localeOrDefault(locale) {
  return Object.values(LOCALES).includes(locale) ? locale : DEFAULT_LOCALE;
}

function text(value, locale = DEFAULT_LOCALE) {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "object") {
    return value[locale] ?? value[DEFAULT_LOCALE] ?? "";
  }
  return String(value);
}

function copyObject(value) {
  return JSON.parse(JSON.stringify(value));
}

function localizeRequest(request, locale) {
  return {
    ...request,
    label: text(request.label, locale),
    status: text(request.status, locale),
    serviceArea: text(request.serviceArea, locale),
    due: text(request.due, locale),
    deadlineDisplay: text(request.deadlineDisplay, locale),
    serviceWindow: text(request.serviceWindow, locale),
    role: text(request.role, locale),
    urgency: text(request.urgency, locale),
    source: text(request.source, locale),
    summary: text(request.summary, locale),
    nextStep: text(request.nextStep, locale),
    coordinatorNote: text(request.coordinatorNote, locale),
    workerSafeSummary: text(request.workerSafeSummary, locale),
    employerVisibleStatus: text(request.employerVisibleStatus, locale),
  };
}

function localizeIntakeTemplate(template, locale) {
  return {
    ...template,
    type: text(template.type, locale),
    source: text(template.source, locale),
    capturedBy: text(template.capturedBy, locale),
    status: text(template.status, locale),
    continuityNote: text(template.continuityNote, locale),
  };
}

function localizedTimeline(locale) {
  return [...TRANSLATIONS[localeOrDefault(locale)].timelineEntries];
}

function localizedMilestones(locale) {
  return DEMO_DATA.employerMilestones.map((milestone) => ({
    ...milestone,
    label: text(milestone.label, locale),
    note: text(milestone.note, locale),
  }));
}

const WORKFLOW_TIMESTAMPS = Object.freeze(["11:18", "11:24", "11:31", "11:38", "11:44", "11:51"]);

function nextWorkflowTimestamp(cursor) {
  return WORKFLOW_TIMESTAMPS[Math.min(cursor, WORKFLOW_TIMESTAMPS.length - 1)];
}

function workflowPresentationState(actionKey, locale, fallbackStatus, fallbackNextStep) {
  const strings = getLocaleStrings(locale);
  if (actionKey === "mark-review-complete") {
    return {
      status: strings.workflowStateReviewComplete,
      nextStep: strings.workflowNextReviewComplete,
    };
  }
  if (actionKey === "set-waiting-on-employer") {
    return {
      status: strings.workflowStateWaitingOnEmployer,
      nextStep: strings.workflowNextWaitingOnEmployer,
    };
  }
  if (actionKey === "prepare-worker-outreach") {
    return {
      status: strings.workflowStateWorkerOutreach,
      nextStep: strings.workflowNextWorkerOutreach,
    };
  }

  return {
    status: fallbackStatus,
    nextStep: fallbackNextStep,
  };
}

function workflowHistoryText(actionKey, locale, requestLabel) {
  const strings = getLocaleStrings(locale);
  const historyMap = {
    "assign-to-me": strings.workflowHistoryAssigned,
    "mark-review-complete": strings.workflowHistoryReviewComplete,
    "set-waiting-on-employer": strings.workflowHistoryWaitingOnEmployer,
    "prepare-worker-outreach": strings.workflowHistoryWorkerOutreach,
  };
  return `${requestLabel} — ${historyMap[actionKey] ?? "updated"}.`;
}

function liveRequestDetails(state, request, locale) {
  const strings = getLocaleStrings(locale);
  const override = state.requestOverrides?.[request.id] ?? {};
  const workflow = workflowPresentationState(
    override.workflowActionKey,
    locale,
    request.status,
    request.nextStep,
  );

  return {
    assignee: override.assignee ?? request.owner,
    status: workflow.status,
    nextStep: workflow.nextStep,
    lastUpdated: override.lastUpdated ?? request.lastUpdated,
    lastActionKey: override.workflowActionKey ?? null,
    summaryTag:
      override.workflowActionKey === "set-waiting-on-employer"
        ? strings.setWaitingOnEmployer
        : override.workflowActionKey === "prepare-worker-outreach"
          ? strings.prepareWorkerOutreach
          : override.workflowActionKey === "mark-review-complete"
            ? strings.markReviewComplete
            : null,
  };
}

function collectCopyStrings(value, locale = DEFAULT_LOCALE, out = []) {
  if (typeof value === "string") {
    out.push(value);
    return out;
  }
  if (value == null) return out;
  if (Array.isArray(value)) {
    for (const item of value) collectCopyStrings(item, locale, out);
    return out;
  }
  if (typeof value === "object") {
    if (Object.prototype.hasOwnProperty.call(value, DEFAULT_LOCALE) || Object.prototype.hasOwnProperty.call(value, LOCALES.es)) {
      out.push(text(value, locale));
      return out;
    }
    for (const key of Object.keys(value)) collectCopyStrings(value[key], locale, out);
  }
  return out;
}

function getRequestById(requestId) {
  return DEMO_DATA.requests.find((request) => request.id === requestId) ?? DEMO_DATA.requests[0];
}

function getTemplateByRecordType(recordType) {
  return DEMO_DATA.intakeTemplates[recordType] ?? null;
}

function getLocaleStrings(locale) {
  return TRANSLATIONS[localeOrDefault(locale)];
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

  if (DEMO_DATA.requests.length !== 5) {
    violations.push("Demo dashboard must include exactly five agency request cards.");
  }

  for (const locale of Object.values(LOCALES)) {
    const copy = [
      text(TRANSLATIONS[locale].notice, locale),
      ...collectCopyStrings(VIEWS, locale),
      ...collectCopyStrings(DEMO_DATA, locale),
      ...collectCopyStrings(TRANSLATIONS[locale], locale),
    ];
    const concatenated = copy.join("\n").toLowerCase();

    for (const term of FORBIDDEN_DECISION_TERMS) {
      const forbiddenMatch = new RegExp(`\\b${term}\\b`, "i");
      if (forbiddenMatch.test(concatenated)) {
        violations.push(`Contract text must not include decision term in ${locale}: ${term}`);
      }
    }

    const addressPattern = /\b\d+\s+[^\n,]+\b(street|st|road|rd|avenue|ave|lane|ln|drive|dr|court|ct|way|place|blvd|boulevard|calle|avenida)\b/i;
    if (addressPattern.test(concatenated)) {
      violations.push(`Demo copy must not include street-like address text in ${locale}.`);
    }
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
    requestOverrides: {},
    workflowHistory: [],
    actionCursor: 0,
    locale: DEFAULT_LOCALE,
    workspace: {
      followUpRecorded: false,
      confirmationMessage: null,
      timeline: localizedTimeline(DEFAULT_LOCALE),
    },
  };
}

function translateStateTimeline(state, locale) {
  const strings = getLocaleStrings(locale);
  const followUpRecorded = Boolean(state.workspace?.followUpRecorded);
  const intakeRecords = state.intakeRecords ?? [];
  const timeline = localizedTimeline(locale);

  for (const record of intakeRecords) {
    const template = getTemplateByRecordType(record.recordType);
    if (template) {
      timeline.push(
        `${strings.timelineDraftEnteredPrefix} ${text(template.type, locale).toLowerCase()} ${strings.timelineDraftEnteredMiddle} ${text(template.source, locale)}.`,
      );
    }
  }

  if (followUpRecorded) {
    const selectedRequest = localizeRequest(getRequestById(state.selectedRequestId), locale);
    timeline.push(
      `${strings.timelineCurrentRunPrefix} ${selectedRequest.label} ${strings.timelineCurrentRunBefore} ${selectedRequest.due}.`,
    );
  }

  for (const entry of state.workflowHistory ?? []) {
    timeline.push(entry);
  }

  return timeline;
}

export function setLocale(state, locale) {
  const nextLocale = localeOrDefault(locale);
  const nextState = {
    ...state,
    locale: nextLocale,
    workspace: {
      ...state.workspace,
      timeline: translateStateTimeline(state, nextLocale),
    },
  };

  if (state.workspace?.confirmationMessage) {
    if (state.workspace.followUpRecorded) {
      nextState.workspace.confirmationMessage = getLocaleStrings(nextLocale).confirmationAlreadyShown;
    }
  }

  return nextState;
}

function localizedConfirmationMessage(state, locale) {
  const strings = getLocaleStrings(locale);

  if (state.workspace?.followUpRecorded) {
    return strings.confirmationAlreadyShown;
  }

  return state.workspace?.confirmationMessage ?? null;
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

export function applyWorkflowAction(state, actionKey) {
  const locale = localeOrDefault(state.locale);
  const request = localizeRequest(getRequestById(state.selectedRequestId), locale);
  const timestamp = nextWorkflowTimestamp(state.actionCursor ?? 0);
  const existingOverride = state.requestOverrides?.[request.id] ?? {};

  const nextOverride = {
    ...existingOverride,
    lastUpdated: timestamp,
  };

  if (actionKey === "assign-to-me") {
    nextOverride.assignee = "Marisol R.";
  } else if (
    actionKey === "mark-review-complete" ||
    actionKey === "set-waiting-on-employer" ||
    actionKey === "prepare-worker-outreach"
  ) {
    nextOverride.workflowActionKey = actionKey;
  } else {
    return state;
  }

  const historyEntry = `${timestamp} — ${workflowHistoryText(actionKey, locale, request.label)}`;

  const nextState = {
    ...state,
    actionCursor: (state.actionCursor ?? 0) + 1,
    requestOverrides: {
      ...(state.requestOverrides ?? {}),
      [request.id]: nextOverride,
    },
    workflowHistory: [...(state.workflowHistory ?? []), historyEntry],
    workspace: {
      ...state.workspace,
      confirmationMessage: historyEntry,
    },
  };

  nextState.workspace.timeline = translateStateTimeline(nextState, locale);
  return nextState;
}

export function addSyntheticIntakeRecord(state, recordType) {
  const template = getTemplateByRecordType(recordType);
  if (!template) return state;

  const locale = localeOrDefault(state.locale);
  const strings = getLocaleStrings(locale);
  const intakeRecords = state.intakeRecords ?? [];
  const alreadyAdded = intakeRecords.some((record) => record.id === template.id);

  if (alreadyAdded) {
    return {
      ...state,
      workspace: {
        ...state.workspace,
        confirmationMessage: `${text(template.type, locale)} ${strings.draftAlreadyInQueue}`,
      },
    };
  }

  const nextState = {
    ...state,
    intakeRecords: [...intakeRecords, { id: template.id, recordType }],
    workspace: {
      ...state.workspace,
      confirmationMessage:
        recordType === "employer" ? strings.employerDraftAdded : strings.workerDraftAdded,
    },
  };

  nextState.workspace.timeline = translateStateTimeline(nextState, locale);
  return nextState;
}

export function recordFictionalFollowUp(state) {
  const locale = localeOrDefault(state.locale);
  const strings = getLocaleStrings(locale);
  const selectedRequest = localizeRequest(getRequestById(state.selectedRequestId), locale);
  const workspace = state.workspace ?? createInitialDemoState().workspace;

  if (workspace.followUpRecorded) {
    return {
      ...state,
      workspace: {
        ...workspace,
        followUpRecorded: true,
        confirmationMessage: strings.confirmationAlreadyShown,
        timeline: translateStateTimeline(state, locale),
      },
    };
  }

  const nextState = {
    ...state,
    workspace: {
      ...workspace,
      followUpRecorded: true,
      confirmationMessage: `${strings.timelineCurrentRunPrefix} ${selectedRequest.label}.`,
    },
  };
  nextState.workspace.timeline = translateStateTimeline(nextState, locale);
  return nextState;
}

function ensureValidViewId(viewId) {
  return DEMO_VIEW_SEQUENCE.includes(viewId) ? viewId : VIEWS.dashboard.id;
}

export function renderViewMarkup(state, viewId = state.activeView) {
  const locale = localeOrDefault(state.locale);
  const resolvedViewId = ensureValidViewId(viewId);
  const selectedRequest = localizeRequest(getRequestById(state.selectedRequestId), locale);
  const localizedState = {
    ...state,
    locale,
    workspace: {
      ...(state.workspace ?? {}),
      timeline: translateStateTimeline(state, locale),
    },
  };
  const activeView = {
    dashboard: () => renderDashboardMarkup(localizedState, selectedRequest),
    workspace: () => renderWorkspaceMarkup(localizedState, selectedRequest),
    intake: () => renderIntakeMarkup(localizedState),
    worker: () => renderWorkerMarkup(localizedState, selectedRequest),
    employer: () => renderEmployerMarkup(localizedState, selectedRequest),
  };

  return {
    viewId: resolvedViewId,
    viewTitle: text(VIEWS[resolvedViewId].pageTitle, locale),
    content: activeView[resolvedViewId](),
  };
}

function renderMetricCards(locale) {
  const strings = getLocaleStrings(locale);
  return `
    <section class="metric-grid" aria-label="${strings.metricsAria}">
      ${strings.metrics
        .map(
          (metric) => `
            <article class="metric-card"><span class="metric-value">${metric.value}</span><span class="metric-label">${metric.label}</span></article>
          `,
        )
        .join("")}
    </section>
  `;
}

function deadlineLabelForRequest(request, strings) {
  return request.dueMode === "open" ? strings.openRequestLabel : strings.dueLabel;
}

function renderMyWorkToday(locale) {
  const strings = getLocaleStrings(locale);
  return `
    <aside class="detail-panel" aria-label="${strings.myWorkTodayAria}">
      <p class="eyebrow">${strings.statusShowing}</p>
      <h2>${strings.myWorkTodayHeading}</h2>
      <ol class="timeline-list">
        ${strings.workTodayItems
          .map(
            (item, index) => `
              <li><span class="timeline-index">${index + 1}</span><span>${item}</span></li>
            `,
          )
          .join("")}
      </ol>
    </aside>
  `;
}

function renderRequestSection(title, description, requests, state, locale) {
  if (requests.length === 0) {
    return "";
  }

  return `
    <section class="request-subsection" aria-label="${title}">
      <div class="request-subsection-header">
        <h2>${title}</h2>
        ${description ? `<p>${description}</p>` : ""}
      </div>
      <div class="request-grid">
        ${requests
          .map((request) => renderRequestCard(request, state.selectedRequestId, locale, liveRequestDetails(state, request, locale)))
          .join("")}
      </div>
    </section>
  `;
}

function renderRequestCard(request, selectedRequestId, locale, liveDetails) {
  const strings = getLocaleStrings(locale);
  const selected = request.id === selectedRequestId;
  const urgencyClass =
    request.urgency === strings.high
      ? "status-warning"
      : request.urgency === strings.medium
        ? "status-open"
        : "status-pending";

  return `
    <article class="request-card ${selected ? "selected-card" : ""}" aria-labelledby="${request.id}-heading">
      <div class="card-topline">
        <span class="status-pill ${urgencyClass}">${request.urgency}</span>
        <span class="due-chip">${request.deadlineDisplay ?? `${deadlineLabelForRequest(request, strings)} ${request.due}`}</span>
      </div>
      <h2 id="${request.id}-heading">${request.label}</h2>
      <p>${request.summary}</p>
      <dl class="compact-details">
        <div><dt>${strings.roleLabel}</dt><dd>${request.role}</dd></div>
        <div><dt>${strings.assignedToLabel}</dt><dd>${liveDetails.assignee}</dd></div>
        <div><dt>${strings.statusLabel}</dt><dd>${liveDetails.status}</dd></div>
        <div><dt>${strings.lastUpdatedLabel}</dt><dd>${liveDetails.lastUpdated}</dd></div>
      </dl>
      <button type="button" class="secondary-btn full-width" data-select-request="${request.id}" data-switch="workspace">
        ${strings.requestOverviewAction}
      </button>
    </article>
  `;
}

function renderDashboardMarkup(state, selectedRequest) {
  const locale = localeOrDefault(state.locale);
  const strings = getLocaleStrings(locale);
  const localizedRequests = DEMO_DATA.requests.map((request) => localizeRequest(request, locale));
  const selectedLiveDetails = liveRequestDetails(state, selectedRequest, locale);
  const scheduledRequests = localizedRequests.filter((request) => request.dueMode !== "open");
  const openSearchRequests = localizedRequests.filter((request) => request.dueMode === "open");

  return `
    ${renderMetricCards(locale)}
    <section class="dashboard-layout" aria-label="${strings.dashboardContentAria}">
      ${renderMyWorkToday(locale)}
      <div class="request-list" aria-label="${strings.requestCardsAria}">
        ${renderRequestSection(strings.activeRequestsHeading, "", scheduledRequests, state, locale)}
        ${renderRequestSection(strings.openSearchesHeading, strings.openSearchesDescription, openSearchRequests, state, locale)}
      </div>
      <aside class="detail-panel" aria-label="${strings.requestDetailAria}">
        <p class="eyebrow">${strings.selectedRequestEyebrow}</p>
        <h2>${selectedRequest.label}</h2>
        <p>${selectedRequest.summary}</p>
        <dl class="detail-list">
          <div><dt>${strings.employerLabel}</dt><dd>${selectedRequest.employerName}</dd></div>
          <div><dt>${strings.broadAreaLabel}</dt><dd>${selectedRequest.serviceArea}</dd></div>
          <div><dt>${deadlineLabelForRequest(selectedRequest, strings)}</dt><dd>${selectedRequest.due}</dd></div>
          <div><dt>${strings.statusLabel}</dt><dd>${selectedLiveDetails.status}</dd></div>
          <div><dt>${strings.assignedToLabel}</dt><dd>${selectedLiveDetails.assignee}</dd></div>
          <div><dt>${strings.lastUpdatedLabel}</dt><dd>${selectedLiveDetails.lastUpdated}</dd></div>
          <div><dt>${strings.nextStaffStepLabel}</dt><dd>${selectedLiveDetails.nextStep}</dd></div>
        </dl>
        <div class="button-row">
          <button type="button" class="primary-btn" data-switch="workspace">${strings.fullRequestDetail}</button>
          <button type="button" class="secondary-btn" data-switch="intake">${strings.addWorkerOrEmployer}</button>
          <button type="button" class="secondary-btn" data-switch="worker">${strings.previewWorkerView}</button>
          <button type="button" class="secondary-btn" data-switch="employer">${strings.previewEmployerView}</button>
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

function renderIntakeQueue(records, locale) {
  const strings = getLocaleStrings(locale);
  if (records.length === 0) {
    return `<p class="empty-state">${strings.noSyntheticRecords}</p>`;
  }

  return `
    <div class="queue-list">
      ${records
        .map((record) => {
          const template = localizeIntakeTemplate(getTemplateByRecordType(record.recordType), locale);
          return `
            <article class="queue-card">
              <p class="eyebrow">${template.type === strings.employerLabel ? strings.employerDraftEyebrow : strings.workerDraftEyebrow}</p>
              <h3>${template.name}</h3>
              <dl class="detail-list">
                <div><dt>${strings.sourceLabel}</dt><dd>${template.source}</dd></div>
                <div><dt>${strings.capturedByLabel}</dt><dd>${template.capturedBy}</dd></div>
                <div><dt>${strings.statusLabel}</dt><dd>${template.status}</dd></div>
                <div><dt>${strings.continuityLabel}</dt><dd>${template.continuityNote}</dd></div>
              </dl>
            </article>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderIntakeMarkup(state) {
  const locale = localeOrDefault(state.locale);
  const strings = getLocaleStrings(locale);
  const intakeRecords = state.intakeRecords ?? [];
  const employerTemplate = localizeIntakeTemplate(DEMO_DATA.intakeTemplates.employer, locale);
  const workerTemplate = localizeIntakeTemplate(DEMO_DATA.intakeTemplates.worker, locale);

  return `
    <section class="workspace-hero">
      <div>
        <p class="eyebrow">${strings.firstRolloutWorkflow}</p>
        <h2>${strings.manualRecordIntake}</h2>
        <p>${strings.manualRecordIntro}</p>
      </div>
      <dl class="deadline-card">
        <div><dt>${strings.currentPaperBacklogLabel}</dt><dd>${strings.currentPaperBacklogValue}</dd></div>
        <div><dt>${strings.continuityShownLabel}</dt><dd>${strings.continuityShownValue}</dd></div>
        <div><dt>${strings.liveDatabaseLabel}</dt><dd>${strings.liveDatabaseValue}</dd></div>
      </dl>
    </section>

    <section class="two-column" aria-label="${strings.manualIntakeActionsAria}">
      <article class="action-card">
        <h2>${strings.addEmployerFromPaper}</h2>
        <p>${strings.addEmployerDescription}</p>
        <dl class="detail-list">
          <div><dt>${strings.nameLabel}</dt><dd>${employerTemplate.name}</dd></div>
          <div><dt>${strings.sourceLabel}</dt><dd>${employerTemplate.source}</dd></div>
          <div><dt>${strings.reviewStateLabel}</dt><dd>${employerTemplate.status}</dd></div>
        </dl>
        <button type="button" class="primary-btn" data-action="add-employer-record">${strings.addEmployerDraft}</button>
      </article>

      <article class="action-card">
        <h2>${strings.addWorkerFromPacket}</h2>
        <p>${strings.addWorkerDescription}</p>
        <dl class="detail-list">
          <div><dt>${strings.nameLabel}</dt><dd>${workerTemplate.name}</dd></div>
          <div><dt>${strings.sourceLabel}</dt><dd>${workerTemplate.source}</dd></div>
          <div><dt>${strings.reviewStateLabel}</dt><dd>${workerTemplate.status}</dd></div>
        </dl>
        <button type="button" class="primary-btn" data-action="add-worker-record">${strings.addWorkerDraft}</button>
      </article>
    </section>

    <section class="timeline" aria-label="${strings.queuePreviewAria}">
      <h2>${strings.queuePreviewHeading}</h2>
      ${renderIntakeQueue(intakeRecords, locale)}
      <div class="button-row inline-actions">
        <button type="button" class="secondary-btn" data-switch="dashboard">${strings.backToDashboard}</button>
        <button type="button" class="secondary-btn" data-switch="workspace">${strings.openRequestDetail}</button>
      </div>
    </section>
  `;
}

function renderWorkspaceMarkup(state, selectedRequest) {
  const locale = localeOrDefault(state.locale);
  const strings = getLocaleStrings(locale);
  const selectedLiveDetails = liveRequestDetails(state, selectedRequest, locale);
  return `
    <section class="workspace-hero">
      <div>
        <p class="eyebrow">${strings.agencyOwnedRequestDetail}</p>
        <h2>${selectedRequest.label}</h2>
        <p>${selectedRequest.summary}</p>
      </div>
      <dl class="deadline-card">
        <div><dt>${deadlineLabelForRequest(selectedRequest, strings)}</dt><dd>${selectedRequest.due}</dd></div>
        <div><dt>${strings.serviceWindowLabel}</dt><dd>${selectedRequest.serviceWindow}</dd></div>
        <div><dt>${strings.coordinatorLabel}</dt><dd>${selectedRequest.owner}</dd></div>
      </dl>
    </section>

    <section class="two-column" aria-label="${strings.requestDetailSectionsAria}">
      <article class="action-card">
        <h2>${strings.staffCoordinationDetail}</h2>
        <dl class="detail-list">
          <div><dt>${strings.employerLabel}</dt><dd>${selectedRequest.employerName}</dd></div>
          <div><dt>${strings.broadAreaLabel}</dt><dd>${selectedRequest.serviceArea}</dd></div>
          <div><dt>${strings.requestedRoleLabel}</dt><dd>${selectedRequest.role}</dd></div>
          <div><dt>${strings.quantityLabel}</dt><dd>${selectedRequest.count}</dd></div>
          <div><dt>${strings.assignedToLabel}</dt><dd>${selectedLiveDetails.assignee}</dd></div>
          <div><dt>${strings.statusLabel}</dt><dd>${selectedLiveDetails.status}</dd></div>
          <div><dt>${strings.lastUpdatedLabel}</dt><dd>${selectedLiveDetails.lastUpdated}</dd></div>
          <div><dt>${strings.nextStaffStepLabel}</dt><dd>${selectedLiveDetails.nextStep}</dd></div>
          <div><dt>${strings.sourceLabel}</dt><dd>${selectedRequest.source}</dd></div>
          <div><dt>${strings.coordinatorNoteLabel}</dt><dd>${selectedRequest.coordinatorNote}</dd></div>
        </dl>
      </article>
      <article class="action-card">
        <h2>${strings.presentationActions}</h2>
        <p>${strings.presentationActionsDescription}</p>
        <div class="button-stack">
          <button type="button" class="primary-btn" data-action="assign-to-me">${strings.assignToMe}</button>
          <button type="button" class="secondary-btn" data-action="mark-review-complete">${strings.markReviewComplete}</button>
          <button type="button" class="secondary-btn" data-action="set-waiting-on-employer">${strings.setWaitingOnEmployer}</button>
          <button type="button" class="secondary-btn" data-action="prepare-worker-outreach">${strings.prepareWorkerOutreach}</button>
          <button type="button" class="primary-btn" data-action="record-follow-up">${strings.showStaffFollowUp}</button>
          <button type="button" class="secondary-btn" data-switch="intake">${strings.addWorkerOrEmployer}</button>
          <button type="button" class="secondary-btn" data-switch="worker">${strings.openWorkerRequestPage}</button>
          <button type="button" class="secondary-btn" data-switch="employer">${strings.openEmployerStatusPage}</button>
          <button type="button" class="secondary-btn" data-switch="dashboard">${strings.backToDashboard}</button>
        </div>
      </article>
    </section>

    <section class="timeline" aria-label="${strings.timelineAria}">
      <h2>${strings.staffActivityTrail}</h2>
      ${renderTimeline(state.workspace.timeline)}
    </section>
  `;
}

function renderWorkerMarkup(state, selectedRequest) {
  const locale = localeOrDefault(state.locale);
  const strings = getLocaleStrings(locale);
  const requestPreview = state.workerInterestOpened
    ? `
      <section class="detail-panel inline-detail" aria-label="${strings.workerPreviewAria}">
        <p class="eyebrow">${strings.interestRequestPreview}</p>
        <h2>${strings.workerWouldReviewNext}</h2>
        <dl class="detail-list">
          <div><dt>${strings.opportunityLabel}</dt><dd>${selectedRequest.role}</dd></div>
          <div><dt>${strings.broadAreaLabel}</dt><dd>${selectedRequest.serviceArea}</dd></div>
          <div><dt>${strings.scheduleLabel}</dt><dd>${selectedRequest.serviceWindow}</dd></div>
          <div><dt>${strings.agencyNextStepLabel}</dt><dd>${strings.agencyNextStepValue}</dd></div>
        </dl>
      </section>
    `
    : "";

  return `
    <section class="workspace-hero">
      <div>
        <p class="eyebrow">${strings.workerFacingPreview}</p>
        <h2>${selectedRequest.role}</h2>
        <p>${selectedRequest.workerSafeSummary}</p>
      </div>
      <dl class="deadline-card">
        <div><dt>${strings.areaLabel}</dt><dd>${selectedRequest.serviceArea}</dd></div>
        <div><dt>${strings.scheduleLabel}</dt><dd>${selectedRequest.serviceWindow}</dd></div>
        <div><dt>${strings.staffContactLabel}</dt><dd>Agency coordinator</dd></div>
      </dl>
    </section>
    <section class="action-card">
      <h2>${strings.workerRequestAction}</h2>
      <p>${strings.workerRequestActionDescription}</p>
      <button type="button" class="primary-btn" data-action="open-worker-interest">${text(DEMO_DATA.worker.actionText, locale)}</button>
      <button type="button" class="secondary-btn" data-switch="workspace">${strings.backToRequestDetail}</button>
    </section>
    ${requestPreview}
  `;
}

function renderEmployerMarkup(state, selectedRequest) {
  const locale = localeOrDefault(state.locale);
  const strings = getLocaleStrings(locale);
  const updatePreview = state.employerUpdateOpened
    ? `
      <section class="detail-panel inline-detail" aria-label="${strings.employerUpdateAria}">
        <p class="eyebrow">${strings.employerUpdateDraft}</p>
        <h2>${strings.nextUpdateVisible}</h2>
        <p>${strings.employerUpdateBodyPrefix} ${selectedRequest.due}${strings.employerUpdateBodySuffix}</p>
        <p>${strings.employerPrivacyNote}</p>
      </section>
    `
    : "";

  return `
    <section class="workspace-hero">
      <div>
        <p class="eyebrow">${strings.employerFacingStatus}</p>
        <h2>${selectedRequest.employerName}</h2>
        <p>${selectedRequest.employerVisibleStatus}: ${selectedRequest.summary}</p>
      </div>
      <dl class="deadline-card">
        <div><dt>${strings.requestLabel}</dt><dd>${selectedRequest.label}</dd></div>
        <div><dt>${strings.serviceWindowLabel}</dt><dd>${selectedRequest.serviceWindow}</dd></div>
        <div><dt>${strings.nextUpdateLabel}</dt><dd>${selectedRequest.due}</dd></div>
      </dl>
    </section>
    <section class="two-column" aria-label="${strings.employerSectionsAria}">
      <article class="action-card">
        <h2>${strings.visibleMilestoneTrail}</h2>
        <ol class="timeline-list">
          ${localizedMilestones(locale)
            .map(
              (milestone, index) => `
                <li><span class="timeline-index">${index + 1}</span><span><strong>${milestone.when} — ${milestone.label}:</strong> ${milestone.note}</span></li>
              `,
            )
            .join("")}
        </ol>
      </article>
      <article class="action-card">
        <h2>${strings.employerSafeRequestSummary}</h2>
        <dl class="detail-list">
          <div><dt>${strings.statusLabel}</dt><dd>${selectedRequest.employerVisibleStatus}</dd></div>
          <div><dt>${strings.broadAreaLabel}</dt><dd>${selectedRequest.serviceArea}</dd></div>
          <div><dt>${strings.coordinatorOwnedNextStepLabel}</dt><dd>${selectedRequest.nextStep}</dd></div>
        </dl>
        <div class="button-stack">
          <button type="button" class="primary-btn" data-action="open-employer-update">${strings.updatePreviewAction}</button>
          <button type="button" class="secondary-btn" data-switch="workspace">${strings.backToRequestDetail}</button>
        </div>
      </article>
    </section>
    ${updatePreview}
  `;
}

function setActiveNav(currentViewId, locale) {
  const navButtons = document.querySelectorAll("#demo-navigation [data-switch]");

  for (const button of navButtons) {
    const viewId = button.dataset.switch;
    const isCurrent = viewId === currentViewId;
    button.textContent = text(VIEWS[viewId].navLabel, locale);
    button.classList.toggle("active", isCurrent);
    if (isCurrent) {
      button.setAttribute("aria-current", "page");
    } else {
      button.removeAttribute("aria-current");
    }
  }
}

function setActiveLocale(locale) {
  const localeButtons = document.querySelectorAll("[data-set-locale]");
  for (const button of localeButtons) {
    const isCurrent = button.dataset.setLocale === locale;
    button.classList.toggle("active-locale", isCurrent);
    button.setAttribute("aria-pressed", isCurrent ? "true" : "false");
  }
}

function announceStatus(message) {
  const statusRegion = document.getElementById("demo-status-region");
  if (statusRegion) statusRegion.textContent = message;
}

function updateDocumentTitle(viewId, locale) {
  document.title = `${text(VIEWS[viewId].pageTitle, locale)} — ${getLocaleStrings(locale).localeDocumentTitleSuffix}`;
}

function updateShellCopy(locale) {
  const strings = getLocaleStrings(locale);
  document.documentElement.lang = locale;
  const notice = document.getElementById("demo-notice");
  if (notice) notice.textContent = strings.notice;
  const navNote = document.getElementById("navigation-note");
  if (navNote) navNote.textContent = strings.navDescription;
  const nav = document.getElementById("demo-navigation");
  if (nav) {
    nav.setAttribute("aria-label", strings.navAriaLabel);
    nav.setAttribute("aria-describedby", "navigation-note");
  }
  const skipLink = document.getElementById("skip-link");
  if (skipLink) skipLink.textContent = strings.skipLink;
  const languageLabel = document.getElementById("language-label");
  if (languageLabel) languageLabel.textContent = strings.languageLabel;
  const enButton = document.querySelector('[data-set-locale="en"]');
  if (enButton) enButton.textContent = strings.englishLabel;
  const esButton = document.querySelector('[data-set-locale="es"]');
  if (esButton) esButton.textContent = strings.spanishLabel;
}

function handleDemoInteraction(state, target) {
  const actionElement = target.closest("[data-action], [data-switch], [data-select-request], [data-set-locale]");
  if (!actionElement || actionElement.disabled) return false;

  const nextLocale = actionElement.dataset.setLocale;
  if (nextLocale) {
    Object.assign(state, setLocale(state, nextLocale));
    state.workspace.confirmationMessage = getLocaleStrings(state.locale).languageChanged;
    renderDemoApp(state);
    return true;
  }

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
  if (
    action === "assign-to-me" ||
    action === "mark-review-complete" ||
    action === "set-waiting-on-employer" ||
    action === "prepare-worker-outreach"
  ) {
    Object.assign(state, applyWorkflowAction(state, action));
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
  const languageControls = document.getElementById("demo-language-controls");

  root?.addEventListener("click", (event) => {
    handleDemoInteraction(state, event.target);
  });

  nav?.addEventListener("click", (event) => {
    handleDemoInteraction(state, event.target);
  });

  languageControls?.addEventListener("click", (event) => {
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
  const locale = localeOrDefault(state.locale);
  const resolvedState = {
    ...state,
    locale,
    activeView: ensureValidViewId(state.activeView),
    selectedRequestId: getRequestById(state.selectedRequestId).id,
    intakeRecords: state.intakeRecords ?? [],
    workspace: {
      ...(state.workspace ?? {}),
      timeline: translateStateTimeline(state, locale),
      confirmationMessage: state.workspace?.confirmationMessage ?? null,
    },
  };

  Object.assign(state, resolvedState);

  const root = document.getElementById("demo-root");
  if (!root) return;

  updateShellCopy(locale);
  root.innerHTML = renderDemoContainer(resolvedState);
  root.querySelector("#demo-view-heading")?.focus();

  const currentView = resolvedState.activeView;
  const selectedRequest = localizeRequest(getRequestById(resolvedState.selectedRequestId), locale);
  const strings = getLocaleStrings(locale);
  const statusText =
    resolvedState.workspace.confirmationMessage ??
    `${text(VIEWS[currentView].navLabel, locale)} ${strings.statusShowing} ${selectedRequest.label}.`;
  announceStatus(statusText);
  setActiveNav(currentView, locale);
  setActiveLocale(locale);
  updateDocumentTitle(currentView, locale);
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
