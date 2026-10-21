export type StaffAccountLanguage = 'en' | 'es';

const permissionLabels: Record<string, { en: string; es: string }> = {
  'calendar_import:manage': { en: 'Calendar Import: Manage', es: 'Importacion de calendario: Administrar' },
  'canonical:review': { en: 'Canonical Records: Review', es: 'Registros canonicos: Revisar' },
  'employer:draft:create': { en: 'Employers: Create Draft', es: 'Empleadores: Crear borrador' },
  'employer:draft:revise': { en: 'Employers: Revise Draft', es: 'Empleadores: Revisar borrador' },
  'employer:read': { en: 'Employers: Read', es: 'Empleadores: Leer' },
  'employer_address:correct': { en: 'Employer Addresses: Correct', es: 'Direcciones de empleadores: Corregir' },
  'employer_contact:details:correct': { en: 'Employer Contact Details: Correct', es: 'Detalles de contactos de empleadores: Corregir' },
  'employer_contact:details:read': { en: 'Employer Contact Details: Read', es: 'Detalles de contactos de empleadores: Leer' },
  'employer_contact:draft:create': { en: 'Employer Contacts: Create Draft', es: 'Contactos de empleadores: Crear borrador' },
  'employer_contact:read': { en: 'Employer Contacts: Read', es: 'Contactos de empleadores: Leer' },
  'intake:draft:create': { en: 'Intakes: Create Draft', es: 'Admisiones: Crear borrador' },
  'intake:draft:revise': { en: 'Intakes: Revise Draft', es: 'Admisiones: Revisar borrador' },
  'intake:finalize': { en: 'Intakes: Finalize', es: 'Admisiones: Finalizar' },
  'intake:follow_up': { en: 'Intakes: Follow Up', es: 'Admisiones: Seguimiento' },
  'intake:link': { en: 'Intakes: Link Records', es: 'Admisiones: Vincular registros' },
  'intake:read': { en: 'Intakes: Read', es: 'Admisiones: Leer' },
  'intake:restricted_history:read': { en: 'Intakes: Read Restricted History', es: 'Admisiones: Leer historial restringido' },
  'intake:review': { en: 'Intakes: Review', es: 'Admisiones: Revisar' },
  'party_address:read': { en: 'Party Addresses: Read', es: 'Direcciones: Leer' },
  'party_address:write': { en: 'Party Addresses: Write', es: 'Direcciones: Escribir' },
  'shift_need:create': { en: 'Shift Needs: Create', es: 'Necesidades de turnos: Crear' },
  'shift_need:read': { en: 'Shift Needs: Read', es: 'Necesidades de turnos: Leer' },
  'shift_need:submit_review': { en: 'Shift Needs: Submit for Review', es: 'Necesidades de turnos: Enviar a revision' },
  'staff_account:activate': { en: 'Staff Accounts: Activate', es: 'Cuentas del personal: Activar' },
  'staff_account:create': { en: 'Staff Accounts: Create', es: 'Cuentas del personal: Crear' },
  'staff_account:delegation:grant': { en: 'Staff Accounts: Grant Delegation', es: 'Cuentas del personal: Conceder delegacion' },
  'staff_account:delegation:revoke': { en: 'Staff Accounts: Revoke Delegation', es: 'Cuentas del personal: Revocar delegacion' },
  'staff_account:deprovision': { en: 'Staff Accounts: Deprovision', es: 'Cuentas del personal: Retirar' },
  'staff_account:read': { en: 'Staff Accounts: Read', es: 'Cuentas del personal: Leer' },
  'staff_account:recovery:record': { en: 'Staff Accounts: Record Recovery Evidence', es: 'Cuentas del personal: Registrar recuperacion' },
  'staff_account:session:revoke': { en: 'Staff Accounts: Record Session Revocation', es: 'Cuentas del personal: Registrar revocacion de sesion' },
  'staff_account:signin:reset': { en: 'Staff Accounts: Restart Google Sign-in', es: 'Cuentas del personal: Reiniciar acceso de Google' },
  'staff_account:suspend': { en: 'Staff Accounts: Suspend', es: 'Cuentas del personal: Suspender' },
  'staffing_request:correct': { en: 'Staffing Requests: Correct', es: 'Solicitudes de personal: Corregir' },
  'staffing_request:read': { en: 'Staffing Requests: Read', es: 'Solicitudes de personal: Leer' },
  'staffing_request:submit_review': { en: 'Staffing Requests: Submit for Review', es: 'Solicitudes de personal: Enviar a revision' },
  'worker:correct': { en: 'Workers: Correct', es: 'Trabajadores: Corregir' },
  'worker:read': { en: 'Workers: Read', es: 'Trabajadores: Leer' },
  'worker_contact:correct': { en: 'Worker Contacts: Correct', es: 'Contactos de trabajadores: Corregir' },
  'worker_contact:read': { en: 'Worker Contacts: Read', es: 'Contactos de trabajadores: Leer' },
  'worker_preferences:correct': { en: 'Worker Preferences: Correct', es: 'Preferencias de trabajadores: Corregir' },
  'worker_residence:correct': { en: 'Worker Residences: Correct', es: 'Residencias de trabajadores: Corregir' },
  'worker_residence:read': { en: 'Worker Residences: Read', es: 'Residencias de trabajadores: Leer' },
  'worker_residence:write': { en: 'Worker Residences: Write', es: 'Residencias de trabajadores: Escribir' },
  'work_interest:manage': { en: 'Work Interests: Manage', es: 'Intereses de trabajo: Administrar' },
  'work_interest:read': { en: 'Work Interests: Read', es: 'Intereses de trabajo: Leer' },
  'worksite:correct': { en: 'Worksites: Correct', es: 'Lugares de trabajo: Corregir' },
  'worksite:read': { en: 'Worksites: Read', es: 'Lugares de trabajo: Leer' },
  'worksite_address:read': { en: 'Worksite Addresses: Read', es: 'Direcciones de lugares de trabajo: Leer' },
  'worksite_address:write': { en: 'Worksite Addresses: Write', es: 'Direcciones de lugares de trabajo: Escribir' },
};

function titleCaseToken(value: string) {
  return value
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(' ');
}

export function permissionLabel(permission: string, language: StaffAccountLanguage) {
  const mapped = permissionLabels[permission];
  if (mapped) return mapped[language];
  const [area, ...actions] = permission.split(':');
  if (area === undefined || actions.length === 0) return titleCaseToken(permission);
  return `${titleCaseToken(area)}: ${actions.map(titleCaseToken).join(' ')}`;
}
