export const canonicalMessages = {
  en: {
    discard: 'Discard pending selection', title: 'Match records before finalizing', search: 'Search existing records', query: 'Name to search',
    more: 'More records', choose: 'Choose explicitly', new: 'Create new at finalization',
    party: 'Worker or employer', contacts: 'Contact', worksites: 'Worksite', addresses: 'Business address',
    apply: 'Save selection', unlink: 'Remove saved selection', finalize: 'Finalize intake',
    confirm: 'I confirm this reviewed intake should be finalized.',
    meaning: 'Finalization preserves the reviewed intake and creates or reuses the selected records. Worker information remains self-reported. Employer finalization creates one new draft request; it does not open demand or create shifts.',
    selection: 'Use this final-review step to reuse an existing worker or employer record, or choose Create new at finalization. Selected records stay read-only; the intake candidate remains separate until finalization.',
    ready: 'Save all sections and complete a current review before finalizing.',
    stale: 'Selected records have changed. Search and explicitly select current versions, compare the facts, then review again.',
    saved: 'Saved source references', resolved: 'Selected current facts (read-only)', candidate: 'Intake candidate (retained separately)',
    finalized: 'Finalized intake — read-only', outputs: 'Original finalization references', created: 'Created', reused: 'Reused',
    empty: 'No records found.', selected: 'Pending selection', version: 'Version',
  },
  es: {
    discard: 'Descartar selección pendiente', title: 'Comparar registros antes de finalizar', search: 'Buscar registros existentes', query: 'Nombre para buscar',
    more: 'Más registros', choose: 'Elegir explícitamente', new: 'Crear nuevo al finalizar',
    party: 'Trabajador o empleador', contacts: 'Contacto', worksites: 'Lugar de trabajo', addresses: 'Dirección comercial',
    apply: 'Guardar selección', unlink: 'Quitar selección guardada', finalize: 'Finalizar admisión',
    confirm: 'Confirmo que esta admisión revisada debe finalizarse.',
    meaning: 'La finalización conserva la admisión revisada y crea o reutiliza los registros seleccionados. La información del trabajador sigue siendo autodeclarada. Para empleadores se crea una solicitud nueva en borrador; no se abre demanda ni se crean turnos.',
    selection: 'Use este paso de revisión final para reutilizar un registro existente de trabajador o empleador, o elija Crear nuevo al finalizar. Los registros seleccionados son de solo lectura; la admisión queda separada hasta la finalización.',
    ready: 'Guarde todas las secciones y complete una revisión vigente antes de finalizar.',
    stale: 'Los registros seleccionados cambiaron. Busque y seleccione explícitamente las versiones actuales, compare los datos y vuelva a revisar.',
    saved: 'Referencias de origen guardadas', resolved: 'Datos actuales seleccionados (solo lectura)', candidate: 'Datos de admisión (conservados por separado)',
    finalized: 'Admisión finalizada — solo lectura', outputs: 'Referencias originales de finalización', created: 'Creado', reused: 'Reutilizado',
    empty: 'No se encontraron registros.', selected: 'Selección pendiente', version: 'Versión',
  },
};

export function canonicalLabel(key: string, language: 'en' | 'es'): string {
  const labels: Record<string, readonly [string, string]> = {
    worker: ['Worker', 'Trabajador'], employer: ['Employer', 'Empleador'],
    contact: ['Contact', 'Contacto'], worker_contact: ['Worker contact', 'Contacto del trabajador'],
    employer_contact: ['Employer contact', 'Contacto del empleador'],
    contact_details: ['Contact details', 'Datos de contacto'], employer_contact_details: ['Contact details', 'Datos de contacto'],
    residence: ['Residence', 'Residencia'], worker_residence: ['Residence', 'Residencia'],
    preferences: ['Preferences', 'Preferencias'], worker_preferences: ['Preferences', 'Preferencias'],
    worksite: ['Worksite', 'Lugar de trabajo'], request: ['Draft request', 'Solicitud en borrador'],
    business_address: ['Business address', 'Dirección comercial'], employer_address: ['Business address', 'Dirección comercial'],
    party: ['Worker or employer', 'Trabajador o empleador'],
  };
  return labels[key]?.[language === 'en' ? 0 : 1] ?? key;
}
