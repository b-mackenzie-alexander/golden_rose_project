import { useContext, useEffect, useMemo, useRef, useState } from 'react';
import type { SyntheticEvent } from 'react';

import {
  activateStaffAccount,
  correctStaffAccount,
  createStaffAccount,
  deprovisionStaffAccount,
  grantStaffDelegation,
  listStaffAccounts,
  listStaffAccountEvents,
  listStaffDelegations,
  readStaffAccountDiagnostics,
  recordRecoveryEvidence,
  recordSessionRevocationEvidence,
  revokeStaffDelegation,
  suspendStaffAccount,
  updateStaffAccountGoogleEmail,
} from '../api/staffAccountClient';
import type { StaffAccountDiagnostics, StaffAccount, StaffAccountFailureKind, StaffAccountLifecycleEvent, StaffAccountRole, StaffDelegation } from '../api/staffAccountClient';
import { GoogleStaffSignIn } from '../auth/GoogleStaffSignIn';
import { IconSymbol } from '../dashboard/artwork';
import { useLanguage } from '../i18n/LanguageProvider';
import { permissionLabel } from './permissionLabels';
import { NavigationGuardContext } from '../app/navigationGuardContext';

type AccountAction = 'activate' | 'suspend' | 'deprovision' | 'recovery' | 'session';
type AccountFilter = 'all' | 'active' | 'suspended' | 'deprovisioned' | 'mfa_pending';
type CreateForm = {
  displayName: string;
  providerEmail: string;
  roleName: StaffAccountRole;
  permissionNames: string[];
  mfaEnrolled: boolean;
  reasonText: string;
};
type ActionForm = {
  account: StaffAccount;
  action: AccountAction;
  reasonText: string;
  mfaEnrolled: boolean;
};
type EmailForm = {
  commandId: string;
  locked: boolean;
  uncertain: boolean;
  account: StaffAccount;
  providerEmail: string;
  reasonText: string;
};
type DelegationPanel = {
  account: StaffAccount;
  items: StaffDelegation[];
  loading: boolean;
  permissionName: string;
  expiresAt: string;
  reasonText: string;
  revokeReasonText: string;
  error: string;
};
type HistoryPanel = {
  account: StaffAccount;
  items: StaffAccountLifecycleEvent[];
  loading: boolean;
  error: string;
};

const permissionGroups = [
  {
    label: { en: 'Account administration', es: 'Administracion de cuentas' },
    items: [
      'staff_account:read',
      'staff_account:create',
      'staff_account:activate',
      'staff_account:suspend',
      'staff_account:signin:reset',
      'staff_account:deprovision',
      'staff_account:recovery:record',
      'staff_account:session:revoke',
      'staff_account:delegation:grant',
      'staff_account:delegation:revoke',
    ],
  },
  {
    label: { en: 'Intake workflow', es: 'Flujo de admisiones' },
    items: [
      'intake:read',
      'intake:draft:create',
      'intake:draft:revise',
      'intake:review',
      'intake:follow_up',
      'intake:link',
      'intake:finalize',
      'intake:restricted_history:read',
      'canonical:review',
    ],
  },
  {
    label: { en: 'Worker records', es: 'Registros de trabajadores' },
    items: [
      'worker:read',
      'worker:correct',
      'worker_contact:read',
      'worker_contact:correct',
      'worker_residence:read',
      'worker_residence:write',
      'worker_residence:correct',
      'worker_preferences:correct',
      'work_interest:read',
      'work_interest:manage',
    ],
  },
  {
    label: { en: 'Employer records', es: 'Registros de empleadores' },
    items: [
      'employer:read',
      'employer:draft:create',
      'employer:draft:revise',
      'employer_address:correct',
      'employer_contact:read',
      'employer_contact:draft:create',
      'employer_contact:details:read',
      'employer_contact:details:correct',
      'party_address:read',
      'party_address:write',
      'worksite:read',
      'worksite:correct',
      'worksite_address:read',
      'worksite_address:write',
      'staffing_request:read',
      'staffing_request:submit_review',
      'staffing_request:correct',
    ],
  },
  {
    label: { en: 'Calendar and requests', es: 'Calendario y solicitudes' },
    items: [
      'calendar_import:manage',
      'shift_need:create',
      'shift_need:read',
      'shift_need:submit_review',
    ],
  },
] as const;

const allPermissionNames = permissionGroups.flatMap((group) => group.items);
const permissionOrder: Map<string, number> = new Map(allPermissionNames.map((permission, index) => [permission, index]));

function sortPermissions(permissions: readonly string[]) {
  return Array.from(new Set(permissions)).sort((left, right) => {
    const leftOrder = permissionOrder.get(left) ?? Number.MAX_SAFE_INTEGER;
    const rightOrder = permissionOrder.get(right) ?? Number.MAX_SAFE_INTEGER;
    if (leftOrder !== rightOrder) return leftOrder - rightOrder;
    return left.localeCompare(right);
  });
}

const permissionProfiles = [
  {
    id: 'owner',
    label: { en: 'Owner / full access', es: 'Propietaria / acceso completo' },
    summary: {
      en: 'All staff, intake, worker, employer, jobsite, calendar, and request tools.',
      es: 'Todas las herramientas de personal, admisiones, trabajadores, empleadores, lugares, calendario y solicitudes.',
    },
    roleName: 'owner',
    permissions: allPermissionNames,
  },
  {
    id: 'residential_intake',
    label: { en: 'Residential intake operator', es: 'Operadora de admision residencial' },
    summary: {
      en: 'Worker and residential employer intake without jobsite or staff-account administration.',
      es: 'Admisiones de trabajadores y empleadores residenciales sin lugares de trabajo ni administracion de cuentas.',
    },
    roleName: 'operations_staff',
    permissions: [
      'intake:read',
      'intake:draft:create',
      'intake:draft:revise',
      'intake:review',
      'intake:follow_up',
      'worker:read',
      'worker:correct',
      'worker_contact:read',
      'worker_contact:correct',
      'worker_residence:read',
      'worker_residence:write',
      'worker_residence:correct',
      'worker_preferences:correct',
      'employer:read',
      'employer:draft:create',
      'employer:draft:revise',
      'employer_address:correct',
      'employer_contact:read',
      'employer_contact:draft:create',
      'employer_contact:details:read',
      'employer_contact:details:correct',
      'party_address:read',
      'party_address:write',
      'work_interest:read',
    ],
  },
  {
    id: 'jobsite_requests',
    label: { en: 'Jobsite and request coordinator', es: 'Coordinadora de lugares y solicitudes' },
    summary: {
      en: 'Employer worksites, staffing requests, and shift needs without worker residential details.',
      es: 'Lugares de empleadores, solicitudes de personal y necesidades de turnos sin detalles residenciales de trabajadores.',
    },
    roleName: 'operations_staff',
    permissions: [
      'employer:read',
      'employer_contact:read',
      'employer_contact:details:read',
      'worksite:read',
      'worksite:correct',
      'worksite_address:read',
      'worksite_address:write',
      'staffing_request:read',
      'staffing_request:submit_review',
      'staffing_request:correct',
      'shift_need:create',
      'shift_need:read',
      'shift_need:submit_review',
    ],
  },
  {
    id: 'account_manager',
    label: { en: 'Account manager', es: 'Gerente de cuentas' },
    summary: {
      en: 'Create, activate, suspend, and provision staff accounts without worker or employer records.',
      es: 'Crear, activar, suspender y provisionar cuentas sin registros de trabajadores o empleadores.',
    },
    roleName: 'delegated_manager',
    permissions: [
      'staff_account:read',
      'staff_account:create',
      'staff_account:activate',
      'staff_account:suspend',
      'staff_account:delegation:grant',
      'staff_account:delegation:revoke',
    ],
  },
  {
    id: 'platform_support',
    label: { en: 'Platform support', es: 'Soporte de plataforma' },
    summary: {
      en: 'Technical account visibility and evidence recording without operational worker or employer data.',
      es: 'Visibilidad tecnica y registro de evidencia sin datos operativos de trabajadores o empleadores.',
    },
    roleName: 'platform_administrator',
    permissions: [
      'staff_account:read',
      'staff_account:recovery:record',
      'staff_account:session:revoke',
    ],
  },
] as const satisfies readonly {
  id: string;
  label: { en: string; es: string };
  summary: { en: string; es: string };
  roleName: StaffAccountRole;
  permissions: readonly string[];
}[];

const provisioningAddOns = [
  {
    id: 'calendar_import',
    label: { en: 'Google Calendar import', es: 'Importacion de Google Calendar' },
    permissions: ['calendar_import:manage'],
  },
  {
    id: 'catalog_manager',
    label: { en: 'Work-interest catalog manager', es: 'Administrar catalogo de intereses' },
    permissions: ['work_interest:read', 'work_interest:manage'],
  },
  {
    id: 'intake_finalizer',
    label: { en: 'Intake finalizer', es: 'Finalizar admisiones' },
    permissions: ['intake:read', 'intake:link', 'intake:finalize', 'intake:restricted_history:read', 'canonical:review'],
  },
  {
    id: 'staff_recovery',
    label: { en: 'Recovery/session evidence', es: 'Evidencia de recuperacion/sesion' },
    permissions: ['staff_account:read', 'staff_account:recovery:record', 'staff_account:session:revoke'],
  },
] as const;

const permissionCoverage = [
  {
    label: { en: 'Account admin', es: 'Admin cuentas' },
    permissions: ['staff_account:read', 'staff_account:create', 'staff_account:activate'],
  },
  {
    label: { en: 'Residential intake', es: 'Admision residencial' },
    permissions: ['intake:read', 'intake:draft:create', 'intake:draft:revise', 'worker:read', 'worker_residence:read', 'worker_residence:write', 'employer:read', 'party_address:write'],
  },
  {
    label: { en: 'Jobsite requests', es: 'Solicitudes de lugar' },
    permissions: ['employer:read', 'worksite:read', 'worksite_address:read', 'worksite_address:write', 'staffing_request:read', 'shift_need:read'],
  },
  {
    label: { en: 'Calendar import', es: 'Importar calendario' },
    permissions: ['calendar_import:manage'],
  },
] as const;

const roleLabels: Record<StaffAccountRole, { en: string; es: string }> = {
  owner: { en: 'Owner', es: 'Propietaria' },
  delegated_manager: { en: 'Delegated manager', es: 'Gerente delegada' },
  operations_staff: { en: 'Operations staff', es: 'Personal operativo' },
  platform_administrator: { en: 'Platform administrator', es: 'Administrador de plataforma' },
};

const statusLabels = {
  active: { en: 'Active', es: 'Activa' },
  suspended: { en: 'Suspended', es: 'Suspendida' },
  deprovisioned: { en: 'Deprovisioned', es: 'Retirada' },
};

const filterLabels: Record<AccountFilter, { en: string; es: string }> = {
  all: { en: 'All accounts', es: 'Todas las cuentas' },
  active: { en: 'Active', es: 'Activas' },
  suspended: { en: 'Suspended onboarding', es: 'Incorporacion suspendida' },
  deprovisioned: { en: 'Deprovisioned', es: 'Retiradas' },
  mfa_pending: { en: 'MFA pending', es: 'MFA pendiente' },
};

const actionLabels: Record<AccountAction, { en: string; es: string }> = {
  activate: { en: 'Activate', es: 'Activar' },
  suspend: { en: 'Suspend', es: 'Suspender' },
  deprovision: { en: 'Deprovision', es: 'Retirar' },
  recovery: { en: 'Record recovery evidence', es: 'Registrar evidencia de recuperacion' },
  session: { en: 'Record session revocation evidence', es: 'Registrar evidencia de sesion revocada' },
};

const eventLabels: Record<StaffAccountLifecycleEvent['eventType'], { en: string; es: string }> = {
  'staff_account.created': { en: 'Account created', es: 'Cuenta creada' },
  'staff_account.activated': { en: 'Account activated', es: 'Cuenta activada' },
  'staff_account.suspended': { en: 'Account suspended', es: 'Cuenta suspendida' },
  'staff_account.deprovisioned': { en: 'Account deprovisioned', es: 'Cuenta retirada' },
  'staff_account.access_updated': { en: 'Access updated', es: 'Acceso actualizado' },
  'staff_account.binding_verified': { en: 'Google identity verified', es: 'Identidad de Google verificada' },
  'staff_account.binding_restarted': { en: 'Google onboarding restarted', es: 'Incorporación de Google reiniciada' },
  'staff_account.corrected': { en: 'Account corrected', es: 'Cuenta corregida' },
  'staff_account.signin_email_updated': { en: 'Google email updated', es: 'Correo de Google actualizado' },
  'staff_account.recovery_recorded': { en: 'Recovery evidence recorded', es: 'Evidencia de recuperacion registrada' },
  'staff_account.sessions_revoked': { en: 'Session-revocation evidence recorded', es: 'Evidencia de revocacion de sesion registrada' },
};

const failureLabels: Record<StaffAccountFailureKind, { en: string; es: string }> = {
  sign_in_required: { en: 'Sign in with a staff session before managing accounts.', es: 'Inicie sesion del personal antes de administrar cuentas.' },
  authentication_failed: { en: 'The staff session could not be verified. Sign in again through the configured provider.', es: 'No se pudo verificar la sesion del personal. Inicie sesion otra vez con el proveedor configurado.' },
  account_unavailable: { en: 'This staff account is unavailable for account administration.', es: 'Esta cuenta del personal no esta disponible para administrar cuentas.' },
  identity_provider_unavailable: { en: 'The staff identity provider is temporarily unavailable.', es: 'El proveedor de identidad del personal no esta disponible temporalmente.' },
  validation: { en: 'Check the highlighted account fields and try again.', es: 'Revise los campos marcados e intente otra vez.' },
  forbidden: { en: 'This staff session does not have permission for that account action.', es: 'Esta sesion no tiene permiso para esa accion.' },
  not_found: { en: 'The account is no longer available. Reload the list.', es: 'La cuenta ya no esta disponible. Recargue la lista.' },
  stale: { en: 'The account changed in another session. Reload before trying again.', es: 'La cuenta cambio en otra sesion. Recargue antes de intentar otra vez.' },
  unavailable: { en: 'The account service is unavailable. Try again after the connection recovers.', es: 'El servicio de cuentas no esta disponible. Intente cuando se recupere la conexion.' },
  unknown_outcome: { en: 'The outcome is unknown. Retry the original account request before changing the form.', es: 'El resultado es desconocido. Reintente la solicitud original antes de cambiar el formulario.' },
  unexpected: { en: 'The account response could not be used safely.', es: 'La respuesta de cuenta no se pudo usar con seguridad.' },
  delegation_self_grant: { en: 'Temporary delegations are for another staff account. Use Correct to add named permissions to your own account.', es: 'Las delegaciones temporales son para otra cuenta. Use Corregir para agregar permisos nombrados a su propia cuenta.' },
  delegation_permission_unavailable: { en: 'This session cannot delegate a permission it does not currently have. Add the named permission through account correction or ask an authorized owner.', es: 'Esta sesion no puede delegar un permiso que no tiene actualmente. Agregue el permiso nombrado mediante correccion de cuenta o pida ayuda a una propietaria autorizada.' },
  delegation_target_unavailable: { en: 'This staff account cannot receive a delegation in its current state.', es: 'Esta cuenta del personal no puede recibir una delegacion en su estado actual.' },
  delegation_expiration_invalid: { en: 'Choose a future expiration within one year.', es: 'Elija un vencimiento futuro dentro de un ano.' },
};

const emptyCreate: CreateForm = {
  displayName: '',
  providerEmail: '',
  roleName: 'operations_staff',
  permissionNames: ['staff_account:read'],
  mfaEnrolled: false,
  reasonText: '',
};

function createCommandId() {
  return globalThis.crypto.randomUUID();
}

function upsertAccount(accounts: StaffAccount[], account: StaffAccount) {
  const next = accounts.filter((item) => item.staffId !== account.staffId);
  return [account, ...next].sort((a, b) => Date.parse(b.updatedAt) - Date.parse(a.updatedAt));
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

function providerSubjectStatus(account: StaffAccount, language: 'en' | 'es') {
  const labels = {
    pending: { en: 'Waiting for Google sign-in', es: 'Esperando inicio de sesión con Google' },
    legacy_unverified: { en: 'Legacy identity: verification needed', es: 'Identidad anterior: necesita verificación' },
    google_verified: { en: 'Google identity verified', es: 'Identidad de Google verificada' },
  };
  return labels[account.bindingStatus][language];
}

function formatStatusTransition(event: StaffAccountLifecycleEvent, language: 'en' | 'es') {
  const version = language === 'en' ? 'version' : 'version';
  if (event.previousStatus === null || event.previousVersion === null) {
    return language === 'en'
      ? `${statusLabels[event.newStatus][language]}, ${version} ${String(event.newVersion)}`
      : `${statusLabels[event.newStatus][language]}, ${version} ${String(event.newVersion)}`;
  }
  if (event.previousStatus === event.newStatus && event.previousVersion === event.newVersion) {
    return language === 'en'
      ? `Evidence only, unchanged ${version} ${String(event.newVersion)}`
      : `Solo evidencia, ${version} ${String(event.newVersion)} sin cambios`;
  }
  return language === 'en'
    ? `${statusLabels[event.previousStatus][language]} to ${statusLabels[event.newStatus][language]}, ${version} ${String(event.newVersion)}`
    : `${statusLabels[event.previousStatus][language]} a ${statusLabels[event.newStatus][language]}, ${version} ${String(event.newVersion)}`;
}

function isFutureLocal(value: string) {
  const timestamp = Date.parse(value);
  return !Number.isNaN(timestamp) && timestamp > Date.now();
}

function tomorrowLocalValue() {
  const value = new Date(Date.now() + 24 * 60 * 60 * 1000);
  value.setSeconds(0, 0);
  return value.toISOString().slice(0, 16);
}

function failureText(kind: StaffAccountFailureKind, language: 'en' | 'es') {
  return failureLabels[kind][language];
}

function hasPermissions(account: StaffAccount, required: readonly string[]) {
  return required.every((permission) => account.permissionNames.includes(permission));
}

function hasSelectedPermissions(selected: readonly string[], required: readonly string[]) {
  return required.every((permission) => selected.includes(permission));
}

function profileDescription(selected: readonly string[], profile: (typeof permissionProfiles)[number], language: 'en' | 'es') {
  const missingCount = profile.permissions.filter((permission) => !selected.includes(permission)).length;
  if (missingCount === 0) {
    return language === 'en' ? 'Complete in current selection' : 'Completo en la seleccion actual';
  }
  return language === 'en'
    ? `${String(missingCount)} missing from current selection`
    : `Faltan ${String(missingCount)} en la seleccion actual`;
}

function accessSummary(roleName: StaffAccountRole, selected: readonly string[], language: 'en' | 'es') {
  const completeProfiles = permissionProfiles.filter((profile) => profile.roleName === roleName && hasSelectedPermissions(selected, profile.permissions));
  const [firstProfile] = completeProfiles;
  if (firstProfile !== undefined) {
    return language === 'en'
      ? `${firstProfile.label.en}: ${String(selected.length)} durable permissions`
      : `${firstProfile.label.es}: ${String(selected.length)} permisos duraderos`;
  }
  return language === 'en'
    ? `${roleLabels[roleName][language]}: ${String(selected.length)} custom durable permissions`
    : `${roleLabels[roleName][language]}: ${String(selected.length)} permisos duraderos personalizados`;
}

function PermissionChecklist({
  selected,
  onToggle,
  onApplyPermissions,
  language,
}: {
  selected: string[];
  onToggle: (permission: string) => void;
  onApplyPermissions: (permissions: readonly string[], roleName?: StaffAccountRole) => void;
  language: 'en' | 'es';
}) {
  return (
    <>
      <div className="staff-permission-presets" aria-label={language === 'en' ? 'Role permission presets' : 'Perfiles de permisos por rol'}>
        <p>
          {language === 'en'
            ? 'Apply a role preset for the durable tools this person needs, then add or remove one-off provisions below.'
            : 'Aplique un perfil de rol para las herramientas duraderas que necesita la persona; despues agregue o quite provisiones abajo.'}
        </p>
        <div>
          {permissionProfiles.map((profile) => (
            <button
              className="focus-ring"
              data-active={hasSelectedPermissions(selected, profile.permissions) ? 'true' : 'false'}
              key={profile.id}
              type="button"
              onClick={() => { onApplyPermissions(profile.permissions, profile.roleName); }}
            >
              <strong>{profile.label[language]}</strong>
              <span>{profile.summary[language]}</span>
              <small>{profileDescription(selected, profile, language)}</small>
            </button>
          ))}
        </div>
      </div>
      <div className="staff-permission-addons" aria-label={language === 'en' ? 'Provisioning add-ons' : 'Provisiones adicionales'}>
        <p>{language === 'en' ? 'Provisioning add-ons' : 'Provisiones adicionales'}</p>
        <div>
          {provisioningAddOns.map((addOn) => {
            const active = hasSelectedPermissions(selected, addOn.permissions);
            return (
              <button
                className="focus-ring"
                data-active={active ? 'true' : 'false'}
                key={addOn.id}
                type="button"
                onClick={() => {
                  const nextPermissions = active
                    ? selected.filter((permission) => !(addOn.permissions as readonly string[]).includes(permission))
                    : sortPermissions([...selected, ...addOn.permissions]);
                  onApplyPermissions(nextPermissions);
                }}
              >
                {active ? language === 'en' ? 'Remove' : 'Quitar' : language === 'en' ? 'Add' : 'Agregar'} {addOn.label[language]}
              </button>
            );
          })}
        </div>
      </div>
      {permissionGroups.map((group) => (
        <div className="staff-permission-group" key={group.label.en}>
          <p>{group.label[language]}</p>
          {group.items.map((permission) => (
            <label key={permission}>
              <input checked={selected.includes(permission)} type="checkbox" onChange={() => { onToggle(permission); }} />
              <span title={permission}>{permissionLabel(permission, language)}</span>
            </label>
          ))}
        </div>
      ))}
    </>
  );
}

function actionHelp(action: AccountAction, language: 'en' | 'es') {
  if (action === 'recovery') {
    return language === 'en'
      ? 'Evidence only. Identity-provider factor reset stays outside this application.'
      : 'Solo evidencia. El restablecimiento del proveedor de identidad queda fuera de esta aplicacion.';
  }
  if (action === 'session') {
    return language === 'en'
      ? 'Evidence only. This does not confirm provider-side session revocation.'
      : 'Solo evidencia. No confirma revocacion de sesiones en el proveedor.';
  }
  if (action === 'activate') {
    return language === 'en'
      ? 'Activation requires confirmed MFA enrollment.'
      : 'La activacion requiere MFA confirmado.';
  }
  return language === 'en'
    ? 'Lifecycle changes use the current account version.'
    : 'Los cambios usan la version actual de la cuenta.';
}

export function StaffAccountAdmin() {
  const { language } = useLanguage();
  const setNavigationBlocked = useContext(NavigationGuardContext);
  const [emailBusy, setEmailBusy] = useState(false);
  const [accounts, setAccounts] = useState<StaffAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [accountsLoaded, setAccountsLoaded] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [accessFailure, setAccessFailure] = useState<StaffAccountFailureKind | null>(null);
  const [createForm, setCreateForm] = useState<CreateForm>(emptyCreate);
  const [createErrors, setCreateErrors] = useState<Partial<Record<keyof CreateForm, string>>>({});
  const [correctionForm, setCorrectionForm] = useState<(CreateForm & { account: StaffAccount }) | null>(null);
  const [correctionErrors, setCorrectionErrors] = useState<Partial<Record<keyof CreateForm, string>>>({});
  const [emailForm, setEmailForm] = useState<EmailForm | null>(null);
  const [emailErrors, setEmailErrors] = useState<Partial<Record<'providerEmail' | 'reasonText', string>>>({});
  const [actionForm, setActionForm] = useState<ActionForm | null>(null);
  const [actionError, setActionError] = useState('');
  const [delegationPanel, setDelegationPanel] = useState<DelegationPanel | null>(null);
  const [historyPanel, setHistoryPanel] = useState<HistoryPanel | null>(null);
  const [accountFilter, setAccountFilter] = useState<AccountFilter>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const diagnosticGeneration = useRef(0);
  const diagnosticPanelRef = useRef<HTMLElement>(null);
  const [diagnostic, setDiagnostic] = useState<StaffAccount | null>(null);
  const [diagnosticError, setDiagnosticError] = useState('');
  const [diagnosticRights, setDiagnosticRights] = useState<StaffAccountDiagnostics | null>(null);
  const [diagnosticLoading, setDiagnosticLoading] = useState(false);
  useEffect(() => {
    if (diagnostic || diagnosticError) diagnosticPanelRef.current?.focus();
  }, [diagnostic, diagnosticError]);
  async function inspectSignIn(account: StaffAccount) {
    const generation = ++diagnosticGeneration.current;
    setDiagnostic(null); setDiagnosticRights(null); setDiagnosticError(''); setDiagnosticLoading(true);
    const result = await readStaffAccountDiagnostics(account.staffId);
    if (generation !== diagnosticGeneration.current) return;
    if (result.ok) { setDiagnostic(result.value.account); setDiagnosticRights(result.value); }
    else setDiagnosticError(failureText(result.failure.kind, language));
    setDiagnosticLoading(false);
  }
  const activeCount = useMemo(() => accounts.filter((account) => account.lifecycleStatus === 'active').length, [accounts]);
  const suspendedCount = useMemo(() => accounts.filter((account) => account.lifecycleStatus === 'suspended').length, [accounts]);
  const deprovisionedCount = useMemo(() => accounts.filter((account) => account.lifecycleStatus === 'deprovisioned').length, [accounts]);
  const filteredAccounts = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();
    return accounts.filter((account) => {
      const matchesFilter = accountFilter === 'all'
        || (accountFilter === 'active' && account.lifecycleStatus === 'active')
        || (accountFilter === 'suspended' && account.lifecycleStatus === 'suspended')
        || (accountFilter === 'deprovisioned' && account.lifecycleStatus === 'deprovisioned')
        || (accountFilter === 'mfa_pending' && !account.mfaEnrolled && account.lifecycleStatus !== 'deprovisioned');
      const matchesSearch = normalizedSearch.length === 0
        || account.displayName.toLowerCase().includes(normalizedSearch)
        || (account.providerEmail?.toLowerCase().includes(normalizedSearch) ?? false);
      return matchesFilter && matchesSearch;
    });
  }, [accountFilter, accounts, searchTerm]);

  async function reloadAccounts() {
    diagnosticGeneration.current++; setDiagnostic(null); setDiagnosticRights(null); setDiagnosticLoading(false); setDiagnosticError('');
    setLoading(true);
    setError('');
    setAccessFailure(null);
    const result = await listStaffAccounts();
    if (result.ok) {
      setAccounts(result.value);
      setAccountsLoaded(true);
    } else {
      setAccountsLoaded(false);
      diagnosticGeneration.current++; setDiagnostic(null); setDiagnosticRights(null); setDiagnosticLoading(false); setDiagnosticError('');
      setAccounts([]);
      setAccessFailure(result.failure.kind);
      setError(failureText(result.failure.kind, language));
    }
    setLoading(false);
  }

  useEffect(() => {
    const generations = diagnosticGeneration;
    let cancelled = false;
    void Promise.resolve().then(() => { if (!cancelled) setLoading(true); });
    void listStaffAccounts().then((result) => {
      if (cancelled) return;
      generations.current++; setDiagnostic(null); setDiagnosticRights(null); setDiagnosticLoading(false); setDiagnosticError('');
      if (result.ok) {
        setAccounts(result.value);
        setAccountsLoaded(true);
        setError('');
        setAccessFailure(null);
      } else {
        setAccounts([]);
        setAccountsLoaded(false);
        setAccessFailure(result.failure.kind);
        setError(failureText(result.failure.kind, language));
      }
      setLoading(false);
    });
    return () => {
      cancelled = true; generations.current++;
    };
  }, [language]);

  useEffect(() => {
    setNavigationBlocked?.(Boolean(emailForm?.locked));
    return () => { setNavigationBlocked?.(false); };
  }, [emailForm?.locked, setNavigationBlocked]);

  useEffect(() => {
    if (!emailForm?.locked) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); };
    window.addEventListener('beforeunload', warn);
    return () => { window.removeEventListener('beforeunload', warn); };
  }, [emailForm?.locked]);

  const signInRequired = accessFailure === 'sign_in_required' || accessFailure === 'authentication_failed';
  const adminControlsReady = accountsLoaded && !loading;

  function validateAccountForm(form: CreateForm, setErrors: (errors: Partial<Record<keyof CreateForm, string>>) => void, requireEmail = true) {
    const next: Partial<Record<keyof CreateForm, string>> = {};
    if (form.displayName.trim().length === 0) next.displayName = language === 'en' ? 'Display name is required.' : 'Nombre visible requerido.';
    if (requireEmail && form.providerEmail.trim().length === 0) {
      next.providerEmail = language === 'en' ? 'Google sign-in email is required.' : 'Se requiere el correo de inicio de sesión de Google.';
    }
    if (requireEmail && form.providerEmail.trim().length > 0 && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.providerEmail.trim())) {
      next.providerEmail = language === 'en' ? 'Enter a valid Google email address.' : 'Ingrese un correo de Google valido.';
    }
    if (form.permissionNames.length === 0) next.permissionNames = language === 'en' ? 'Select at least one permission.' : 'Seleccione al menos un permiso.';
    if (form.reasonText.trim().length === 0) next.reasonText = language === 'en' ? 'Reason is required.' : 'Motivo requerido.';
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function submitCreate(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    setNotice('');
    setError('');
    if (!validateAccountForm(createForm, setCreateErrors)) return;
    const result = await createStaffAccount({ ...createForm, commandId: createCommandId() });
    if (!result.ok) {
      setError(failureText(result.failure.kind, language));
      return;
    }
    setAccounts((current) => upsertAccount(current, result.value.account));
    setNotice(language === 'en' ? 'Staff account created in suspended onboarding state.' : 'Cuenta creada en estado suspendido para incorporacion.');
    setCreateForm(emptyCreate);
    setCreateErrors({});
  }

  async function submitCorrection(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    setNotice('');
    setError('');
    if (correctionForm === null) return;
    if (!validateAccountForm(correctionForm, setCorrectionErrors, false)) return;
    const result = await correctStaffAccount({
      displayName: correctionForm.displayName,
      roleName: correctionForm.roleName,
      permissionNames: correctionForm.permissionNames,
      reasonText: correctionForm.reasonText,
      staffId: correctionForm.account.staffId,
      expectedVersion: correctionForm.account.version,
      commandId: createCommandId(),
    });
    if (!result.ok) {
      setError(failureText(result.failure.kind, language));
      return;
    }
    setAccounts((current) => upsertAccount(current, result.value.account));
    setNotice(
      correctionForm.account.lifecycleStatus === 'suspended'
        ? language === 'en' ? 'Staff account onboarding details corrected.' : 'Detalles de incorporacion corregidos.'
        : language === 'en' ? 'Staff account access updated.' : 'Acceso de cuenta actualizado.',
    );
    setCorrectionForm(null);
    setCorrectionErrors({});
    await reloadAccounts();
  }

  async function submitEmailUpdate(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    setNotice('');
    setError('');
    if (emailForm === null) return;
    const next: Partial<Record<'providerEmail' | 'reasonText', string>> = {};
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(emailForm.providerEmail.trim())) {
      next.providerEmail = language === 'en' ? 'Enter a valid Google email address.' : 'Ingrese un correo de Google valido.';
    }
    if (emailForm.reasonText.trim().length === 0) {
      next.reasonText = language === 'en' ? 'Reason is required.' : 'Motivo requerido.';
    }
    setEmailErrors(next);
    if (Object.keys(next).length > 0) return;
    if (emailBusy) return;
    setEmailBusy(true);
    setEmailForm({ ...emailForm, locked: true });
    const result = await updateStaffAccountGoogleEmail({
      staffId: emailForm.account.staffId,
      expectedVersion: emailForm.account.version,
      providerEmail: emailForm.providerEmail,
      reasonText: emailForm.reasonText,
      commandId: emailForm.commandId,
    });
    setEmailBusy(false);
    if (!result.ok) {
      if (emailForm.uncertain || result.failure.kind === 'unknown_outcome' || result.failure.kind === 'unavailable') {
        setEmailForm({ ...emailForm, locked: true, uncertain: true });
      } else {
        setEmailForm({ ...emailForm, locked: false, commandId: createCommandId() });
      }
      setError(failureText(result.failure.kind, language));
      return;
    }
    setAccounts((current) => upsertAccount(current, result.value.account));
    setNotice(language === 'en' ? 'Google onboarding restarted. Ask the person to sign in, then confirm MFA and activate.' : 'Incorporación reiniciada. Pida iniciar sesión; luego confirme MFA y active.');
    setEmailForm(null);
    setEmailErrors({});
    await reloadAccounts();
  }

  async function submitAction(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionError('');
    setNotice('');
    if (actionForm === null) return;
    if (actionForm.reasonText.trim().length === 0) {
      setActionError(language === 'en' ? 'Reason is required.' : 'Motivo requerido.');
      return;
    }
    if (actionForm.action === 'activate' && !actionForm.mfaEnrolled) {
      setActionError(language === 'en' ? 'Confirm MFA enrollment before activation.' : 'Confirme la inscripción de MFA antes de activar.');
      return;
    }
    const base = {
      staffId: actionForm.account.staffId,
      expectedVersion: actionForm.account.version,
      reasonText: actionForm.reasonText,
      commandId: createCommandId(),
    };
    const result = actionForm.action === 'activate'
      ? await activateStaffAccount({ ...base, mfaEnrolled: actionForm.mfaEnrolled })
      : actionForm.action === 'suspend'
        ? await suspendStaffAccount(base)
        : actionForm.action === 'deprovision'
          ? await deprovisionStaffAccount(base)
          : actionForm.action === 'recovery'
            ? await recordRecoveryEvidence(base)
            : await recordSessionRevocationEvidence(base);
    if (!result.ok) {
      setActionError(failureText(result.failure.kind, language));
      return;
    }
    setAccounts((current) => upsertAccount(current, result.value.account));
    setNotice(actionLabels[actionForm.action][language]);
    setActionForm(null);
    await reloadAccounts();
  }

  function togglePermission(permission: string) {
    setCreateForm((current) => ({
      ...current,
      permissionNames: current.permissionNames.includes(permission)
        ? current.permissionNames.filter((item) => item !== permission)
        : sortPermissions([...current.permissionNames, permission]),
    }));
  }

  function applyCreatePermissions(permissions: readonly string[], roleName?: StaffAccountRole) {
    setCreateForm((current) => ({
      ...current,
      roleName: roleName ?? current.roleName,
      permissionNames: sortPermissions(permissions),
    }));
  }

  function toggleCorrectionPermission(permission: string) {
    setCorrectionForm((current) => {
      if (current === null) return current;
      return {
        ...current,
        permissionNames: current.permissionNames.includes(permission)
          ? current.permissionNames.filter((item) => item !== permission)
          : sortPermissions([...current.permissionNames, permission]),
      };
    });
  }

  function applyCorrectionPermissions(permissions: readonly string[], roleName?: StaffAccountRole) {
    setCorrectionForm((current) => {
      if (current === null) return current;
      return {
        ...current,
        roleName: roleName ?? current.roleName,
        permissionNames: sortPermissions(permissions),
      };
    });
  }

  function openCorrection(account: StaffAccount) {
    setCorrectionForm({
      account,
      displayName: account.displayName,
      providerEmail: account.providerEmail ?? '',
      roleName: account.roleName,
      permissionNames: sortPermissions(account.permissionNames),
      mfaEnrolled: account.mfaEnrolled,
      reasonText: '',
    });
    setCorrectionErrors({});
  }

  function openEmailUpdate(account: StaffAccount) {
    if (emailForm?.locked) {
      setError(language === 'en' ? 'Resolve the original sign-in restart before starting another.' : 'Resuelva el reinicio original antes de iniciar otro.');
      return;
    }
    setEmailForm({
      commandId: createCommandId(),
      locked: false,
      uncertain: false,
      account,
      providerEmail: account.providerEmail ?? '',
      reasonText: '',
    });
    setEmailErrors({});
  }

  async function openDelegations(account: StaffAccount) {
    const panel: DelegationPanel = {
      account,
      items: [],
      loading: true,
      permissionName: 'intake:read',
      expiresAt: tomorrowLocalValue(),
      reasonText: '',
      revokeReasonText: '',
      error: '',
    };
    setDelegationPanel(panel);
    const result = await listStaffDelegations(account.staffId);
    if (!result.ok) {
      setDelegationPanel({ ...panel, loading: false, error: failureText(result.failure.kind, language) });
      return;
    }
    setDelegationPanel({ ...panel, loading: false, items: result.value });
  }

  async function openHistory(account: StaffAccount) {
    const panel: HistoryPanel = { account, items: [], loading: true, error: '' };
    setHistoryPanel(panel);
    const result = await listStaffAccountEvents(account.staffId);
    if (!result.ok) {
      setHistoryPanel({ ...panel, loading: false, error: failureText(result.failure.kind, language) });
      return;
    }
    setHistoryPanel({ ...panel, loading: false, items: result.value });
  }

  async function submitDelegation(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    if (delegationPanel === null) return;
    if (delegationPanel.reasonText.trim().length === 0 || delegationPanel.expiresAt.trim().length === 0) {
      setDelegationPanel({ ...delegationPanel, error: language === 'en' ? 'Permission, expiration and reason are required.' : 'Permiso, vencimiento y motivo requeridos.' });
      return;
    }
    if (!isFutureLocal(delegationPanel.expiresAt)) {
      setDelegationPanel({ ...delegationPanel, error: language === 'en' ? 'Expiration must be a future date and time.' : 'El vencimiento debe ser una fecha y hora futura.' });
      return;
    }
    const result = await grantStaffDelegation({
      staffId: delegationPanel.account.staffId,
      permissionName: delegationPanel.permissionName,
      expiresAt: new Date(delegationPanel.expiresAt).toISOString(),
      reasonText: delegationPanel.reasonText,
      commandId: createCommandId(),
    });
    if (!result.ok) {
      setDelegationPanel({ ...delegationPanel, error: failureText(result.failure.kind, language) });
      return;
    }
    setDelegationPanel({
      ...delegationPanel,
      items: [result.value.delegation, ...delegationPanel.items.filter((item) => item.delegationId !== result.value.delegation.delegationId)],
      reasonText: '',
      error: '',
    });
    setNotice(language === 'en' ? 'Delegation recorded.' : 'Delegacion registrada.');
  }

  async function submitDelegationRevocation(delegation: StaffDelegation) {
    if (delegationPanel === null) return;
    if (delegationPanel.revokeReasonText.trim().length === 0) {
      setDelegationPanel({ ...delegationPanel, error: language === 'en' ? 'Revocation reason is required.' : 'Motivo de revocacion requerido.' });
      return;
    }
    const result = await revokeStaffDelegation({
      staffId: delegationPanel.account.staffId,
      delegationId: delegation.delegationId,
      reasonText: delegationPanel.revokeReasonText,
      commandId: createCommandId(),
    });
    if (!result.ok) {
      setDelegationPanel({ ...delegationPanel, error: failureText(result.failure.kind, language) });
      return;
    }
    setDelegationPanel({
      ...delegationPanel,
      items: delegationPanel.items.map((item) => item.delegationId === result.value.delegation.delegationId ? result.value.delegation : item),
      revokeReasonText: '',
      error: '',
    });
    setNotice(language === 'en' ? 'Delegation revoked.' : 'Delegacion revocada.');
  }

  return (
    <section aria-labelledby="staff-account-heading" className="staff-account-page">
      <div className="staff-account-header">
        <div>
          <p className="module-preview-eyebrow">{language === 'en' ? 'Staff administration' : 'Administracion del personal'}</p>
          <h2 id="staff-account-heading">{language === 'en' ? 'Staff accounts' : 'Cuentas del personal'}</h2>
        </div>
        <button className="staff-secondary-button focus-ring" type="button" onClick={() => { void reloadAccounts(); }}>
          {language === 'en' ? 'Reload accounts' : 'Recargar cuentas'}
        </button>
      </div>

      <div className="staff-account-metrics" aria-label={language === 'en' ? 'Account lifecycle summary' : 'Resumen de cuentas'}>
        <div><strong>{accounts.length}</strong><span>{language === 'en' ? 'Total accounts' : 'Cuentas totales'}</span></div>
        <div><strong>{activeCount}</strong><span>{language === 'en' ? 'Active' : 'Activas'}</span></div>
        <div><strong>{suspendedCount}</strong><span>{language === 'en' ? 'Suspended' : 'Suspendidas'}</span></div>
        <div><strong>{deprovisionedCount}</strong><span>{language === 'en' ? 'Deprovisioned' : 'Retiradas'}</span></div>
      </div>

      {notice ? <p className="staff-account-notice" role="status">{notice}</p> : null}
      {error ? <p className="staff-account-error" role="alert">{error}</p> : null}
      {signInRequired ? (
        <GoogleStaffSignIn onSignedIn={() => { void reloadAccounts(); }} />
      ) : null}
      {loading ? <p role="status">{language === 'en' ? 'Loading accounts' : 'Cargando cuentas'}</p> : null}

      {adminControlsReady ? (
      <div className="staff-account-layout">
        <section className="staff-account-panel" aria-labelledby="account-list-heading">
          <div className="staff-account-panel-header">
            <h3 id="account-list-heading"><IconSymbol name="workers" /> {language === 'en' ? 'Account lifecycle' : 'Ciclo de cuentas'}</h3>
          </div>
          <div className="staff-account-filters" aria-label={language === 'en' ? 'Account list filters' : 'Filtros de cuentas'}>
            <label>
              <span>{language === 'en' ? 'Find account' : 'Buscar cuenta'}</span>
              <input
                className="focus-ring"
                placeholder={language === 'en' ? 'Name or Google email' : 'Nombre o correo de Google'}
                value={searchTerm}
                onChange={(event) => { setSearchTerm(event.target.value); }}
              />
            </label>
            <label>
              <span>{language === 'en' ? 'Lifecycle filter' : 'Filtro de ciclo'}</span>
              <select className="focus-ring" value={accountFilter} onChange={(event) => { setAccountFilter(event.target.value as AccountFilter); }}>
                {(Object.keys(filterLabels) as AccountFilter[]).map((filter) => (
                  <option key={filter} value={filter}>{filterLabels[filter][language]}</option>
                ))}
              </select>
            </label>
          </div>
          <div className="staff-account-table" role="table" aria-label={language === 'en' ? 'Staff account lifecycle table' : 'Tabla de cuentas'}>
            <div role="row" className="staff-account-row staff-account-row--head">
              <span role="columnheader">{language === 'en' ? 'Staff member' : 'Persona'}</span>
              <span role="columnheader">{language === 'en' ? 'Role / permissions' : 'Rol / permisos'}</span>
              <span role="columnheader">{language === 'en' ? 'State' : 'Estado'}</span>
              <span role="columnheader">{language === 'en' ? 'Updated' : 'Actualizada'}</span>
              <span role="columnheader">{language === 'en' ? 'Actions' : 'Acciones'}</span>
            </div>
            {filteredAccounts.map((account) => (
              <div role="row" className="staff-account-row" key={account.staffId}>
                <span role="cell">
                  <strong>{account.displayName}</strong>
                  {account.providerEmail ? <small>{account.providerEmail}</small> : null}
                  <small>{providerSubjectStatus(account, language)}</small>
                </span>
                <span role="cell">
                  {roleLabels[account.roleName][language]}
                  <small>{accessSummary(account.roleName, account.permissionNames, language)}</small>
                  <small>
                    {language === 'en'
                      ? `${String(account.permissionNames.length)} named permissions`
                      : `${String(account.permissionNames.length)} permisos nombrados`}
                  </small>
                  <div className="staff-permission-coverage" aria-label={language === 'en' ? 'Permission coverage' : 'Cobertura de permisos'}>
                    {permissionCoverage.map((item) => {
                      const ready = hasPermissions(account, item.permissions);
                      return (
                        <span key={item.label.en} data-ready={ready ? 'true' : 'false'}>
                          {item.label[language]}: {ready ? (language === 'en' ? 'ready' : 'lista') : (language === 'en' ? 'missing' : 'faltan')}
                        </span>
                      );
                    })}
                  </div>
                  <details className="staff-permission-details">
                    <summary>{language === 'en' ? 'Named permissions' : 'Permisos nombrados'}</summary>
                    <ul>
                      {account.permissionNames.map((permission) => <li key={permission} title={permission}>{permissionLabel(permission, language)}</li>)}
                    </ul>
                  </details>
                </span>
                <span role="cell">
                  <span className="staff-account-status" data-status={account.lifecycleStatus}>{statusLabels[account.lifecycleStatus][language]}</span>
                  <small>{account.mfaEnrolled ? 'MFA' : language === 'en' ? 'MFA pending before activation' : 'MFA pendiente antes de activar'}</small>
                </span>
                <span role="cell">
                  <time dateTime={account.updatedAt}>{formatDate(account.updatedAt)}</time>
                  <small>{language === 'en' ? `Version ${String(account.version)}` : `Version ${String(account.version)}`}</small>
                </span>
                <span role="cell" className="staff-account-actions">
                  <button className="focus-ring" type="button" onClick={() => { void inspectSignIn(account); }}>{language === 'en' ? 'Sign-in diagnostics' : 'Diagnóstico de acceso'}</button>
                  {account.lifecycleStatus !== 'active' && account.lifecycleStatus !== 'deprovisioned' ? (
                    <button
                      className="focus-ring"
                      disabled={account.bindingStatus !== 'google_verified'}
                      title={
                        account.bindingStatus !== 'google_verified'
                          ? language === 'en'
                            ? 'Waiting for the first verified Google sign-in before activation.'
                            : 'Esperando el primer inicio verificado de Google antes de activar.'
                          : undefined
                      }
                      type="button"
                      onClick={() => { setActionForm({ account, action: 'activate', reasonText: '', mfaEnrolled: false }); }}
                    >
                      {actionLabels.activate[language]}
                    </button>
                  ) : null}
                  {account.lifecycleStatus !== 'deprovisioned' ? (
                    <button className="focus-ring" type="button" onClick={() => { openCorrection(account); }}>{language === 'en' ? 'Manage access' : 'Administrar acceso'}</button>
                  ) : null}
                  {account.lifecycleStatus === 'active' ? (
                    <button className="focus-ring" type="button" onClick={() => { setActionForm({ account, action: 'suspend', reasonText: '', mfaEnrolled: false }); }}>{actionLabels.suspend[language]}</button>
                  ) : null}
                  {account.lifecycleStatus !== 'deprovisioned' ? (
                    <button className="focus-ring" type="button" onClick={() => { setActionForm({ account, action: 'deprovision', reasonText: '', mfaEnrolled: false }); }}>{actionLabels.deprovision[language]}</button>
                  ) : null}
                  {account.lifecycleStatus !== 'deprovisioned' ? (
                    <button className="focus-ring" type="button" onClick={() => { setActionForm({ account, action: 'recovery', reasonText: '', mfaEnrolled: account.mfaEnrolled }); }}>{language === 'en' ? 'Recovery evidence' : 'Evidencia recuperacion'}</button>
                  ) : null}
                  <button className="focus-ring" type="button" onClick={() => { setActionForm({ account, action: 'session', reasonText: '', mfaEnrolled: account.mfaEnrolled }); }}>{language === 'en' ? 'Session evidence' : 'Evidencia sesion'}</button>
                  <button className="focus-ring" type="button" onClick={() => { void openDelegations(account); }}>{language === 'en' ? 'Delegations' : 'Delegaciones'}</button>
                  <button className="focus-ring" type="button" onClick={() => { void openHistory(account); }}>{language === 'en' ? 'History' : 'Historial'}</button>
                </span>
              </div>
            ))}
            {filteredAccounts.length === 0 ? (
              <p className="staff-account-empty">
                {accounts.length === 0
                  ? language === 'en' ? 'No staff accounts are available to this session.' : 'No hay cuentas disponibles para esta sesion.'
                  : language === 'en' ? 'No accounts match this filter.' : 'Ninguna cuenta coincide con este filtro.'}
              </p>
            ) : null}
          </div>
        </section>

        <section className="staff-account-panel" aria-labelledby="create-account-heading">
          <h3 id="create-account-heading"><IconSymbol name="check" /> {language === 'en' ? 'Onboard staff account' : 'Crear cuenta de personal'}</h3>
          <form className="staff-account-form" onSubmit={(event) => { void submitCreate(event); }}>
            <label>
              <span>{language === 'en' ? 'Display name' : 'Nombre visible'}</span>
              <input className="focus-ring" value={createForm.displayName} onChange={(event) => { setCreateForm({ ...createForm, displayName: event.target.value }); }} />
              {createErrors.displayName ? <small role="alert">{createErrors.displayName}</small> : null}
            </label>
            <label>
              <span>{language === 'en' ? 'Google email for sign-in' : 'Correo de Google para iniciar sesion'}</span>
              <input className="focus-ring" type="email" value={createForm.providerEmail} onChange={(event) => { setCreateForm({ ...createForm, providerEmail: event.target.value }); }} />
              {createErrors.providerEmail ? <small role="alert">{createErrors.providerEmail}</small> : null}
            </label>
            <div className="calendar-form-row">
              <label>
                <span>{language === 'en' ? 'Role' : 'Rol'}</span>
                <select className="focus-ring" value={createForm.roleName} onChange={(event) => { setCreateForm({ ...createForm, roleName: event.target.value as StaffAccountRole }); }}>
                  {(Object.keys(roleLabels) as StaffAccountRole[]).map((role) => (
                    <option key={role} value={role}>{roleLabels[role][language]}</option>
                  ))}
                </select>
                <small>
                  {language === 'en'
                    ? 'Role is the staff job label. The permission profile below sets the durable tools.'
                    : 'El rol es la etiqueta del puesto. El perfil de permisos abajo define las herramientas duraderas.'}
                </small>
              </label>
              <label className="staff-checkbox-label">
                <input checked={createForm.mfaEnrolled} type="checkbox" onChange={(event) => { setCreateForm({ ...createForm, mfaEnrolled: event.target.checked }); }} />
                <span>{language === 'en' ? 'MFA already enrolled' : 'MFA ya inscrito'}</span>
              </label>
            </div>
            <fieldset className="staff-permission-fieldset">
              <legend>{language === 'en' ? 'Named permissions' : 'Permisos nombrados'}</legend>
              <p className="staff-account-helper">{accessSummary(createForm.roleName, createForm.permissionNames, language)}</p>
              <PermissionChecklist selected={createForm.permissionNames} onApplyPermissions={applyCreatePermissions} onToggle={togglePermission} language={language} />
              {createErrors.permissionNames ? <small role="alert">{createErrors.permissionNames}</small> : null}
            </fieldset>
            <label>
              <span>{language === 'en' ? 'Reason' : 'Motivo'}</span>
              <textarea className="focus-ring" value={createForm.reasonText} onChange={(event) => { setCreateForm({ ...createForm, reasonText: event.target.value }); }} />
              {createErrors.reasonText ? <small role="alert">{createErrors.reasonText}</small> : null}
            </label>
            <button className="staff-primary-button focus-ring" type="submit">{language === 'en' ? 'Create staff account' : 'Crear cuenta'}</button>
          </form>
        </section>
      </div>
      ) : null}

      {(diagnosticLoading || diagnosticError || diagnostic) ? (
        <section ref={diagnosticPanelRef} tabIndex={-1} className="staff-account-panel focus-ring" aria-label={language === 'en' ? 'Sign-in diagnostics' : 'Diagnóstico de acceso'}>
          <div className="staff-account-panel-header">
          <h3>{language === 'en' ? 'Sign-in diagnostics' : 'Diagnóstico de acceso'}{diagnostic ? `: ${diagnostic.displayName}` : ''}</h3>
          <button className="staff-secondary-button focus-ring" type="button" onClick={() => { diagnosticGeneration.current++; setDiagnosticLoading(false); setDiagnostic(null); setDiagnosticError(''); setDiagnosticRights(null); }}>{language === 'en' ? 'Close diagnostics' : 'Cerrar diagnóstico'}</button>
          </div>
          {diagnosticLoading ? <p role="status">{language === 'en' ? 'Checking account evidence…' : 'Verificando evidencia de la cuenta…'}</p> : null}
          {diagnosticError ? <p role="alert">{diagnosticError}</p> : null}
          {diagnostic ? <>
            <dl>
              <dt>{language === 'en' ? 'Google identity' : 'Identidad de Google'}</dt><dd>{providerSubjectStatus(diagnostic, language)}</dd>
              <dt>{language === 'en' ? 'Verification recorded' : 'Verificación registrada'}</dt><dd>{diagnostic.bindingVerifiedAt ? formatDate(diagnostic.bindingVerifiedAt) : (language === 'en' ? 'No verified evidence recorded' : 'Sin evidencia verificada')}</dd>
              <dt>{language === 'en' ? 'Account state' : 'Estado de cuenta'}</dt><dd>{statusLabels[diagnostic.lifecycleStatus][language]}</dd>
              <dt>MFA</dt><dd>{diagnostic.mfaEnrolled ? (language === 'en' ? 'Enrollment confirmed' : 'Inscripción confirmada') : (language === 'en' ? 'Confirmation required before activation' : 'Se requiere confirmación antes de activar')}</dd>
            </dl>
            <h4>{language === 'en' ? 'Next step' : 'Siguiente paso'}</h4>
            <p>{diagnostic.lifecycleStatus === 'deprovisioned'
              ? (language === 'en' ? 'This account cannot be reactivated. Contact the account administrator.' : 'Esta cuenta no puede reactivarse. Contacte a la administración.')
              : diagnostic.bindingStatus === 'pending'
                ? (language === 'en' ? 'Ask this person to sign in with the assigned Google account. Access stays suspended until a manager confirms MFA and activates it.' : 'Pida iniciar sesión con la cuenta de Google asignada. El acceso sigue suspendido hasta confirmar MFA y activar.')
                : diagnostic.bindingStatus === 'legacy_unverified'
                  ? (language === 'en' ? 'Ask this person to sign in to verify the existing identity. If verification fails, an authorized manager can restart Google sign-in without deleting the account.' : 'Pida iniciar sesión para verificar la identidad anterior. Si falla, una persona autorizada puede reiniciar el acceso sin borrar la cuenta.')
                  : diagnostic.lifecycleStatus !== 'active' || !diagnostic.mfaEnrolled
                    ? (language === 'en' ? 'Google identity is verified. Confirm MFA enrollment and activate the account when appropriate.' : 'Google verificó la identidad. Confirme MFA y active la cuenta cuando corresponda.')
                    : (language === 'en' ? 'Account evidence permits sign-in. If access fails, check the selected Google account and obtain a new browser credential. Permissions for individual tools are reviewed separately.' : 'La evidencia permite el acceso. Si falla, revise la cuenta de Google seleccionada y obtenga una credencial nueva. Revise por separado los permisos de herramientas.')}</p>
            <p>{language === 'en' ? 'This checks Golden Rose account evidence. It does not inspect Google passwords, reset factors, or revoke Google sessions.' : 'Este diagnóstico revisa evidencia de Golden Rose. No inspecciona contraseñas, restablece factores ni revoca sesiones de Google.'}</p>
            <p>{diagnosticRights?.canRestartSignin
              ? (language === 'en' ? 'You can restart Google onboarding for this account.' : 'Puede reiniciar la incorporación de Google para esta cuenta.')
              : diagnosticRights?.restartUnavailableReason === 'self_reset'
                ? (language === 'en' ? 'Use another authorized administrator for your own sign-in recovery.' : 'Use otra cuenta administrativa autorizada para recuperar su propio acceso.')
                : diagnosticRights?.restartUnavailableReason === 'deprovisioned'
                  ? (language === 'en' ? 'Recovery is unavailable for a deprovisioned account.' : 'No se puede recuperar una cuenta retirada.')
                  : (language === 'en' ? 'Recovery requires the Google sign-in recovery permission. Ask an authorized administrator.' : 'La recuperación requiere el permiso correspondiente. Pida ayuda a una persona autorizada.')}</p>
            <div className="staff-account-actions">
            <button className="staff-secondary-button focus-ring" type="button" disabled={!diagnosticRights?.canRestartSignin} onClick={() => { openEmailUpdate(diagnostic); }}>{language === 'en' ? 'Restart Google sign-in' : 'Reiniciar inicio de Google'}</button>
            <button className="staff-secondary-button focus-ring" type="button" disabled={!diagnosticRights?.canActivate} onClick={() => { setActionForm({ account: diagnostic, action: 'activate', reasonText: '', mfaEnrolled: false }); }}>{language === 'en' ? 'Activate verified account' : 'Activar cuenta verificada'}</button>
            <button className="staff-secondary-button focus-ring" type="button" onClick={() => { void inspectSignIn(diagnostic); }}>{language === 'en' ? 'Refresh diagnostics' : 'Actualizar diagnóstico'}</button>
            </div>
          </> : null}
        </section>
      ) : null}

      {correctionForm ? (
        <section className="staff-account-panel staff-action-panel" aria-labelledby="account-correction-heading">
          <div className="staff-account-panel-header">
            <h3 id="account-correction-heading">
              {correctionForm.account.lifecycleStatus === 'suspended'
                ? language === 'en' ? 'Correct onboarding' : 'Corregir incorporacion'
                : language === 'en' ? 'Manage access' : 'Administrar acceso'}: {correctionForm.account.displayName}
            </h3>
            <button className="staff-secondary-button focus-ring" type="button" onClick={() => { setCorrectionForm(null); }}>{language === 'en' ? 'Close' : 'Cerrar'}</button>
          </div>
          <p className="staff-account-helper">
            {language === 'en'
              ? 'Use this for permanent role and permission changes. Named permissions selected here replace this account permissions. Temporary coverage belongs in Delegations.'
              : 'Use esto para cambios permanentes de rol y permisos. Los permisos nombrados seleccionados aqui reemplazan los permisos de esta cuenta. La cobertura temporal pertenece a Delegaciones.'}
          </p>
          <form className="staff-account-form" onSubmit={(event) => { void submitCorrection(event); }}>
            <label>
              <span>{language === 'en' ? 'Display name' : 'Nombre visible'}</span>
              <input className="focus-ring" value={correctionForm.displayName} onChange={(event) => { setCorrectionForm({ ...correctionForm, displayName: event.target.value }); }} />
              {correctionErrors.displayName ? <small role="alert">{correctionErrors.displayName}</small> : null}
            </label>
            <div className="calendar-form-row">
              <label>
                <span>{language === 'en' ? 'Role' : 'Rol'}</span>
                <select className="focus-ring" value={correctionForm.roleName} onChange={(event) => { setCorrectionForm({ ...correctionForm, roleName: event.target.value as StaffAccountRole }); }}>
                  {(Object.keys(roleLabels) as StaffAccountRole[]).map((role) => (
                    <option key={role} value={role}>{roleLabels[role][language]}</option>
                  ))}
                </select>
                <small>
                  {language === 'en'
                    ? 'Role is the staff job label. The permission profile below sets the durable tools.'
                    : 'El rol es la etiqueta del puesto. El perfil de permisos abajo define las herramientas duraderas.'}
                </small>
              </label>
            </div>
            <fieldset className="staff-permission-fieldset">
              <legend>{language === 'en' ? 'Named permissions' : 'Permisos nombrados'}</legend>
              <p className="staff-account-helper">{accessSummary(correctionForm.roleName, correctionForm.permissionNames, language)}</p>
              <PermissionChecklist selected={correctionForm.permissionNames} onApplyPermissions={applyCorrectionPermissions} onToggle={toggleCorrectionPermission} language={language} />
              {correctionErrors.permissionNames ? <small role="alert">{correctionErrors.permissionNames}</small> : null}
            </fieldset>
            <label>
              <span>{language === 'en' ? 'Reason' : 'Motivo'}</span>
              <textarea className="focus-ring" value={correctionForm.reasonText} onChange={(event) => { setCorrectionForm({ ...correctionForm, reasonText: event.target.value }); }} />
              {correctionErrors.reasonText ? <small role="alert">{correctionErrors.reasonText}</small> : null}
            </label>
            <button className="staff-primary-button focus-ring" type="submit">{language === 'en' ? 'Save correction' : 'Guardar correccion'}</button>
          </form>
        </section>
      ) : null}

      {emailForm ? (
        <section className="staff-account-panel staff-action-panel" aria-labelledby="account-email-heading">
          <div className="staff-account-panel-header">
            <h3 id="account-email-heading">{language === 'en' ? 'Restart Google sign-in' : 'Reiniciar inicio de Google'}: {emailForm.account.displayName}</h3>
            <button className="staff-secondary-button focus-ring" type="button" disabled={emailForm.locked} onClick={() => { setEmailForm(null); }}>{language === 'en' ? 'Close' : 'Cerrar'}</button>
          </div>
          <p className="staff-account-helper">
            {language === 'en'
              ? 'Restart sign-in using this email or a corrected email. Access will be suspended until the person signs in with Google and an authorized manager confirms MFA and activates the account. Permissions and history are preserved. This does not sign the person out of Google.'
              : 'Reinicie el acceso con este correo o uno corregido. La cuenta queda suspendida hasta verificar Google y confirmar MFA y activación. Se conservan permisos e historial. No se cierra la sesión de Google.'}
          </p>
          <form className="staff-account-form" onSubmit={(event) => { void submitEmailUpdate(event); }}>
            <label>
              <span>{language === 'en' ? 'Google email for sign-in' : 'Correo de Google para iniciar sesion'}</span>
              <input className="focus-ring" type="email" disabled={emailForm.locked} value={emailForm.providerEmail} onChange={(event) => { setEmailForm({ ...emailForm, providerEmail: event.target.value }); }} />
              {emailErrors.providerEmail ? <small role="alert">{emailErrors.providerEmail}</small> : null}
            </label>
            <label>
              <span>{language === 'en' ? 'Reason' : 'Motivo'}</span>
              <textarea className="focus-ring" disabled={emailForm.locked} value={emailForm.reasonText} onChange={(event) => { setEmailForm({ ...emailForm, reasonText: event.target.value }); }} />
              {emailErrors.reasonText ? <small role="alert">{emailErrors.reasonText}</small> : null}
            </label>
            <button className="staff-primary-button focus-ring" type="submit" disabled={emailBusy}>{emailForm.locked ? (language === 'en' ? 'Retry original restart' : 'Reintentar reinicio original') : (language === 'en' ? 'Restart onboarding' : 'Reiniciar incorporación')}</button>
          </form>
        </section>
      ) : null}

      {actionForm ? (
        <section className="staff-account-panel staff-action-panel" aria-labelledby="account-action-heading">
          <div className="staff-account-panel-header">
            <h3 id="account-action-heading">{actionLabels[actionForm.action][language]}: {actionForm.account.displayName}</h3>
            <button className="staff-secondary-button focus-ring" type="button" onClick={() => { setActionForm(null); }}>{language === 'en' ? 'Close' : 'Cerrar'}</button>
          </div>
          <p>{actionHelp(actionForm.action, language)}</p>
          {actionError ? <p className="staff-account-error" role="alert">{actionError}</p> : null}
          <form className="staff-account-form" onSubmit={(event) => { void submitAction(event); }}>
            {actionForm.action === 'activate' ? (
              <label className="staff-checkbox-label">
                <input checked={actionForm.mfaEnrolled} type="checkbox" onChange={(event) => { setActionForm({ ...actionForm, mfaEnrolled: event.target.checked }); }} />
                <span>{language === 'en' ? 'MFA enrollment confirmed' : 'MFA confirmado'}</span>
              </label>
            ) : null}
            <label>
              <span>{language === 'en' ? 'Reason' : 'Motivo'}</span>
              <textarea className="focus-ring" value={actionForm.reasonText} onChange={(event) => { setActionForm({ ...actionForm, reasonText: event.target.value }); }} />
            </label>
            <button className="staff-primary-button focus-ring" type="submit">{actionLabels[actionForm.action][language]}</button>
          </form>
        </section>
      ) : null}

      {historyPanel ? (
        <section className="staff-account-panel staff-action-panel" aria-labelledby="account-history-heading">
          <div className="staff-account-panel-header">
            <h3 id="account-history-heading">{language === 'en' ? 'Account history' : 'Historial de cuenta'}: {historyPanel.account.displayName}</h3>
            <button className="staff-secondary-button focus-ring" type="button" onClick={() => { setHistoryPanel(null); }}>{language === 'en' ? 'Close' : 'Cerrar'}</button>
          </div>
          <p className="staff-account-helper">
            {language === 'en'
              ? 'This timeline records application evidence and lifecycle decisions. Recovery and session entries do not confirm provider-side reset or revocation.'
              : 'Esta linea de tiempo registra evidencia de la aplicacion y decisiones de ciclo. Recuperacion y sesion no confirman restablecimiento o revocacion en el proveedor.'}
          </p>
          {historyPanel.loading ? <p>{language === 'en' ? 'Loading' : 'Cargando'}</p> : null}
          {historyPanel.error ? <p className="staff-account-error" role="alert">{historyPanel.error}</p> : null}
          <div className="staff-account-history-list" aria-label={language === 'en' ? 'Account evidence history' : 'Historial de evidencia de cuenta'}>
            {historyPanel.items.map((event) => (
              <article className="staff-account-history-row" key={event.eventId}>
                <div>
                  <strong>{eventLabels[event.eventType][language]}</strong>
                  <small>
                    <time dateTime={event.occurredAt}>{formatDate(event.occurredAt)}</time>
                    {' · '}
                    {formatStatusTransition(event, language)}
                  </small>
                </div>
                <p>{event.reasonText}</p>
                <small>{language === 'en' ? 'Actor' : 'Actor'} {event.actorId}</small>
              </article>
            ))}
            {!historyPanel.loading && historyPanel.items.length === 0 ? (
              <p className="staff-account-empty">{language === 'en' ? 'No lifecycle evidence has been recorded for this account.' : 'No hay evidencia de ciclo registrada para esta cuenta.'}</p>
            ) : null}
          </div>
        </section>
      ) : null}

      {delegationPanel ? (
        <section className="staff-account-panel staff-action-panel" aria-labelledby="delegation-heading">
          <div className="staff-account-panel-header">
            <h3 id="delegation-heading">{language === 'en' ? 'Delegations' : 'Delegaciones'}: {delegationPanel.account.displayName}</h3>
            <button className="staff-secondary-button focus-ring" type="button" onClick={() => { setDelegationPanel(null); }}>{language === 'en' ? 'Close' : 'Cerrar'}</button>
          </div>
          <p className="staff-account-helper">
            {language === 'en'
              ? 'Delegations are temporary add-ons for coverage. Use Manage access for permanent role or permission changes.'
              : 'Las delegaciones son permisos temporales para cobertura. Use Administrar acceso para cambios permanentes de rol o permisos.'}
          </p>
          {delegationPanel.loading ? <p>{language === 'en' ? 'Loading' : 'Cargando'}</p> : null}
          {delegationPanel.error ? <p className="staff-account-error" role="alert">{delegationPanel.error}</p> : null}
          <div className="staff-delegation-list" aria-label={language === 'en' ? 'Staff delegations' : 'Delegaciones del personal'}>
            {delegationPanel.items.map((delegation) => (
              <div className="staff-delegation-row" key={delegation.delegationId}>
                <span>
                  <strong title={delegation.permissionName}>{permissionLabel(delegation.permissionName, language)}</strong>
                  <small>{language === 'en' ? 'Global scope' : 'Alcance global'}</small>
                </span>
                <span>
                  <time dateTime={delegation.expiresAt}>{formatDate(delegation.expiresAt)}</time>
                  <small>{delegation.revokedAt ? (language === 'en' ? 'Revoked' : 'Revocada') : (language === 'en' ? 'Active until' : 'Activa hasta')}</small>
                </span>
                <span>
                  {delegation.revokedAt ? (
                    <small>{delegation.revocationReason}</small>
                  ) : (
                    <button className="focus-ring" type="button" onClick={() => { void submitDelegationRevocation(delegation); }}>{language === 'en' ? 'Revoke' : 'Revocar'}</button>
                  )}
                </span>
              </div>
            ))}
            {!delegationPanel.loading && delegationPanel.items.length === 0 ? (
              <p className="staff-account-empty">{language === 'en' ? 'No delegations recorded for this account.' : 'No hay delegaciones registradas para esta cuenta.'}</p>
            ) : null}
          </div>
          <form className="staff-account-form" onSubmit={(event) => { void submitDelegation(event); }}>
            <div className="calendar-form-row">
              <label>
                <span>{language === 'en' ? 'Permission' : 'Permiso'}</span>
                <select className="focus-ring" value={delegationPanel.permissionName} onChange={(event) => { setDelegationPanel({ ...delegationPanel, permissionName: event.target.value }); }}>
                  {permissionGroups.map((group) => (
                    <optgroup key={group.label.en} label={group.label[language]}>
                      {group.items.map((permission) => <option key={permission} value={permission}>{permissionLabel(permission, language)}</option>)}
                    </optgroup>
                  ))}
                </select>
              </label>
              <label>
                <span>{language === 'en' ? 'Expires' : 'Vence'}</span>
                <input className="focus-ring" type="datetime-local" value={delegationPanel.expiresAt} onChange={(event) => { setDelegationPanel({ ...delegationPanel, expiresAt: event.target.value }); }} />
              </label>
            </div>
            <label>
              <span>{language === 'en' ? 'Reason' : 'Motivo'}</span>
              <textarea className="focus-ring" value={delegationPanel.reasonText} onChange={(event) => { setDelegationPanel({ ...delegationPanel, reasonText: event.target.value }); }} />
            </label>
            <label>
              <span>{language === 'en' ? 'Revocation reason' : 'Motivo de revocacion'}</span>
              <textarea className="focus-ring" value={delegationPanel.revokeReasonText} onChange={(event) => { setDelegationPanel({ ...delegationPanel, revokeReasonText: event.target.value }); }} />
            </label>
            <button className="staff-primary-button focus-ring" type="submit">{language === 'en' ? 'Grant delegation' : 'Conceder delegacion'}</button>
          </form>
        </section>
      ) : null}
    </section>
  );
}
