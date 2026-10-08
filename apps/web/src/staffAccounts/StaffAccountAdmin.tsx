import { useEffect, useMemo, useState } from 'react';
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
  recordRecoveryEvidence,
  recordSessionRevocationEvidence,
  revokeStaffDelegation,
  suspendStaffAccount,
  updateStaffAccountGoogleEmail,
} from '../api/staffAccountClient';
import type { StaffAccount, StaffAccountFailureKind, StaffAccountLifecycleEvent, StaffAccountRole, StaffDelegation } from '../api/staffAccountClient';
import { GoogleStaffSignIn } from '../auth/GoogleStaffSignIn';
import { IconSymbol } from '../dashboard/artwork';
import { useLanguage } from '../i18n/LanguageProvider';

type AccountAction = 'activate' | 'suspend' | 'deprovision' | 'recovery' | 'session';
type AccountFilter = 'all' | 'active' | 'suspended' | 'deprovisioned' | 'mfa_pending';
type CreateForm = {
  displayName: string;
  providerEmail: string;
  providerSubject: string;
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

const permissions = [
  'staff_account:read',
  'staff_account:create',
  'staff_account:activate',
  'staff_account:suspend',
  'staff_account:deprovision',
  'staff_account:recovery:record',
  'staff_account:session:revoke',
  'staff_account:delegation:grant',
  'staff_account:delegation:revoke',
  'intake:read',
  'worker:read',
  'employer:read',
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
};

const emptyCreate: CreateForm = {
  displayName: '',
  providerEmail: '',
  providerSubject: '',
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

function isPendingProviderSubject(value: string) {
  return value.startsWith('pending-google-email:');
}

function providerSubjectStatus(account: StaffAccount, language: 'en' | 'es') {
  if (isPendingProviderSubject(account.providerSubject)) {
    return language === 'en' ? 'Waiting for verified Google sign-in' : 'Esperando inicio de Google verificado';
  }
  return language === 'en' ? 'Google sign-in binding recorded' : 'Inicio con Google vinculado';
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
    setLoading(true);
    setError('');
    setAccessFailure(null);
    const result = await listStaffAccounts();
    if (result.ok) {
      setAccounts(result.value);
      setAccountsLoaded(true);
    } else {
      setAccountsLoaded(false);
      setAccounts([]);
      setAccessFailure(result.failure.kind);
      setError(failureText(result.failure.kind, language));
    }
    setLoading(false);
  }

  useEffect(() => {
    let cancelled = false;
    void listStaffAccounts().then((result) => {
      if (cancelled) return;
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
      cancelled = true;
    };
  }, [language]);

  const signInRequired = accessFailure === 'sign_in_required' || accessFailure === 'authentication_failed';
  const adminControlsReady = accountsLoaded;

  function validateAccountForm(form: CreateForm, setErrors: (errors: Partial<Record<keyof CreateForm, string>>) => void) {
    const next: Partial<Record<keyof CreateForm, string>> = {};
    if (form.displayName.trim().length === 0) next.displayName = language === 'en' ? 'Display name is required.' : 'Nombre visible requerido.';
    if (form.providerEmail.trim().length === 0 && form.providerSubject.trim().length === 0) {
      next.providerEmail = language === 'en' ? 'Google email or provider subject is required.' : 'Correo de Google o sujeto del proveedor requerido.';
    }
    if (form.providerEmail.trim().length > 0 && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.providerEmail.trim())) {
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
    if (!validateAccountForm(correctionForm, setCorrectionErrors)) return;
    const result = await correctStaffAccount({
      ...correctionForm,
      staffId: correctionForm.account.staffId,
      expectedVersion: correctionForm.account.version,
      commandId: createCommandId(),
    });
    if (!result.ok) {
      setError(failureText(result.failure.kind, language));
      return;
    }
    setAccounts((current) => upsertAccount(current, result.value.account));
    setNotice(language === 'en' ? 'Staff account onboarding details corrected.' : 'Detalles de incorporacion corregidos.');
    setCorrectionForm(null);
    setCorrectionErrors({});
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
    const result = await updateStaffAccountGoogleEmail({
      staffId: emailForm.account.staffId,
      expectedVersion: emailForm.account.version,
      providerEmail: emailForm.providerEmail,
      reasonText: emailForm.reasonText,
      commandId: createCommandId(),
    });
    if (!result.ok) {
      setError(failureText(result.failure.kind, language));
      return;
    }
    setAccounts((current) => upsertAccount(current, result.value.account));
    setNotice(language === 'en' ? 'Staff account Google email updated.' : 'Correo de Google actualizado.');
    setEmailForm(null);
    setEmailErrors({});
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
  }

  function togglePermission(permission: string) {
    setCreateForm((current) => ({
      ...current,
      permissionNames: current.permissionNames.includes(permission)
        ? current.permissionNames.filter((item) => item !== permission)
        : [...current.permissionNames, permission],
    }));
  }

  function toggleCorrectionPermission(permission: string) {
    setCorrectionForm((current) => {
      if (current === null) return current;
      return {
        ...current,
        permissionNames: current.permissionNames.includes(permission)
          ? current.permissionNames.filter((item) => item !== permission)
          : [...current.permissionNames, permission],
      };
    });
  }

  function openCorrection(account: StaffAccount) {
    setCorrectionForm({
      account,
      displayName: account.displayName,
      providerEmail: account.providerEmail ?? '',
      providerSubject: isPendingProviderSubject(account.providerSubject) ? '' : account.providerSubject,
      roleName: account.roleName,
      permissionNames: ['staff_account:read'],
      mfaEnrolled: account.mfaEnrolled,
      reasonText: '',
    });
    setCorrectionErrors({});
  }

  function openEmailUpdate(account: StaffAccount) {
    setEmailForm({
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

      {adminControlsReady ? (
      <div className="staff-account-layout">
        <section className="staff-account-panel" aria-labelledby="account-list-heading">
          <div className="staff-account-panel-header">
            <h3 id="account-list-heading"><IconSymbol name="workers" /> {language === 'en' ? 'Account lifecycle' : 'Ciclo de cuentas'}</h3>
            {loading ? <span>{language === 'en' ? 'Loading' : 'Cargando'}</span> : null}
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
              <span role="columnheader">{language === 'en' ? 'Role' : 'Rol'}</span>
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
                <span role="cell">{roleLabels[account.roleName][language]}</span>
                <span role="cell">
                  <span className="staff-account-status" data-status={account.lifecycleStatus}>{statusLabels[account.lifecycleStatus][language]}</span>
                  <small>{account.mfaEnrolled ? 'MFA' : language === 'en' ? 'MFA pending before activation' : 'MFA pendiente antes de activar'}</small>
                </span>
                <span role="cell">
                  <time dateTime={account.updatedAt}>{formatDate(account.updatedAt)}</time>
                  <small>{language === 'en' ? `Version ${String(account.version)}` : `Version ${String(account.version)}`}</small>
                </span>
                <span role="cell" className="staff-account-actions">
                  {account.lifecycleStatus !== 'active' && account.lifecycleStatus !== 'deprovisioned' ? (
                    <button
                      className="focus-ring"
                      disabled={isPendingProviderSubject(account.providerSubject)}
                      title={
                        isPendingProviderSubject(account.providerSubject)
                          ? language === 'en'
                            ? 'Waiting for the first verified Google sign-in before activation.'
                            : 'Esperando el primer inicio verificado de Google antes de activar.'
                          : undefined
                      }
                      type="button"
                      onClick={() => { setActionForm({ account, action: 'activate', reasonText: '', mfaEnrolled: true }); }}
                    >
                      {actionLabels.activate[language]}
                    </button>
                  ) : null}
                  {account.lifecycleStatus === 'suspended' ? (
                    <button className="focus-ring" type="button" onClick={() => { openCorrection(account); }}>{language === 'en' ? 'Correct' : 'Corregir'}</button>
                  ) : null}
                  {account.lifecycleStatus !== 'deprovisioned' ? (
                    <button className="focus-ring" type="button" onClick={() => { openEmailUpdate(account); }}>{language === 'en' ? 'Google email' : 'Correo Google'}</button>
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
            {!loading && filteredAccounts.length === 0 ? (
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
            <label>
              <span>{language === 'en' ? 'Provider subject, if already known' : 'Sujeto del proveedor, si ya se conoce'}</span>
              <input className="focus-ring" value={createForm.providerSubject} onChange={(event) => { setCreateForm({ ...createForm, providerSubject: event.target.value }); }} />
              <small>
                {language === 'en'
                  ? 'Leave blank for normal Google email onboarding. The stable sign-in subject binds after the person signs in once.'
                  : 'Dejelo vacio para incorporacion normal por correo de Google. El sujeto estable se vincula despues del primer inicio.'}
              </small>
              {createErrors.providerSubject ? <small role="alert">{createErrors.providerSubject}</small> : null}
            </label>
            <div className="calendar-form-row">
              <label>
                <span>{language === 'en' ? 'Role' : 'Rol'}</span>
                <select className="focus-ring" value={createForm.roleName} onChange={(event) => { setCreateForm({ ...createForm, roleName: event.target.value as StaffAccountRole }); }}>
                  {(Object.keys(roleLabels) as StaffAccountRole[]).map((role) => (
                    <option key={role} value={role}>{roleLabels[role][language]}</option>
                  ))}
                </select>
              </label>
              <label className="staff-checkbox-label">
                <input checked={createForm.mfaEnrolled} type="checkbox" onChange={(event) => { setCreateForm({ ...createForm, mfaEnrolled: event.target.checked }); }} />
                <span>{language === 'en' ? 'MFA already enrolled' : 'MFA ya inscrito'}</span>
              </label>
            </div>
            <fieldset className="staff-permission-fieldset">
              <legend>{language === 'en' ? 'Named permissions' : 'Permisos nombrados'}</legend>
              {permissions.map((permission) => (
                <label key={permission}>
                  <input checked={createForm.permissionNames.includes(permission)} type="checkbox" onChange={() => { togglePermission(permission); }} />
                  <span>{permission}</span>
                </label>
              ))}
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

      {correctionForm ? (
        <section className="staff-account-panel staff-action-panel" aria-labelledby="account-correction-heading">
          <div className="staff-account-panel-header">
            <h3 id="account-correction-heading">{language === 'en' ? 'Correct onboarding' : 'Corregir incorporacion'}: {correctionForm.account.displayName}</h3>
            <button className="staff-secondary-button focus-ring" type="button" onClick={() => { setCorrectionForm(null); }}>{language === 'en' ? 'Close' : 'Cerrar'}</button>
          </div>
          <p className="staff-account-helper">
            {language === 'en'
              ? 'Correct suspended onboarding details before activation. Named permissions selected here replace the suspended account permissions. Deprovision accounts that should not remain usable.'
              : 'Corrija detalles de incorporacion suspendida antes de activar. Los permisos nombrados seleccionados aqui reemplazan los permisos de la cuenta suspendida. Retire cuentas que no deben quedar utilizables.'}
          </p>
          <form className="staff-account-form" onSubmit={(event) => { void submitCorrection(event); }}>
            <label>
              <span>{language === 'en' ? 'Display name' : 'Nombre visible'}</span>
              <input className="focus-ring" value={correctionForm.displayName} onChange={(event) => { setCorrectionForm({ ...correctionForm, displayName: event.target.value }); }} />
              {correctionErrors.displayName ? <small role="alert">{correctionErrors.displayName}</small> : null}
            </label>
            <label>
              <span>{language === 'en' ? 'Google email for sign-in' : 'Correo de Google para iniciar sesion'}</span>
              <input className="focus-ring" type="email" value={correctionForm.providerEmail} onChange={(event) => { setCorrectionForm({ ...correctionForm, providerEmail: event.target.value }); }} />
              {correctionErrors.providerEmail ? <small role="alert">{correctionErrors.providerEmail}</small> : null}
            </label>
            <label>
              <span>{language === 'en' ? 'Provider subject, if already known' : 'Sujeto del proveedor, si ya se conoce'}</span>
              <input className="focus-ring" value={correctionForm.providerSubject} onChange={(event) => { setCorrectionForm({ ...correctionForm, providerSubject: event.target.value }); }} />
              <small>
                {language === 'en'
                  ? 'Leave blank to keep this account waiting for the first verified Google sign-in.'
                  : 'Dejelo vacio para mantener la cuenta esperando el primer inicio de Google verificado.'}
              </small>
              {correctionErrors.providerSubject ? <small role="alert">{correctionErrors.providerSubject}</small> : null}
            </label>
            <div className="calendar-form-row">
              <label>
                <span>{language === 'en' ? 'Role' : 'Rol'}</span>
                <select className="focus-ring" value={correctionForm.roleName} onChange={(event) => { setCorrectionForm({ ...correctionForm, roleName: event.target.value as StaffAccountRole }); }}>
                  {(Object.keys(roleLabels) as StaffAccountRole[]).map((role) => (
                    <option key={role} value={role}>{roleLabels[role][language]}</option>
                  ))}
                </select>
              </label>
              <label className="staff-checkbox-label">
                <input checked={correctionForm.mfaEnrolled} type="checkbox" onChange={(event) => { setCorrectionForm({ ...correctionForm, mfaEnrolled: event.target.checked }); }} />
                <span>{language === 'en' ? 'MFA already enrolled' : 'MFA ya inscrito'}</span>
              </label>
            </div>
            <fieldset className="staff-permission-fieldset">
              <legend>{language === 'en' ? 'Named permissions' : 'Permisos nombrados'}</legend>
              {permissions.map((permission) => (
                <label key={permission}>
                  <input checked={correctionForm.permissionNames.includes(permission)} type="checkbox" onChange={() => { toggleCorrectionPermission(permission); }} />
                  <span>{permission}</span>
                </label>
              ))}
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
            <h3 id="account-email-heading">{language === 'en' ? 'Manage Google email' : 'Administrar correo de Google'}: {emailForm.account.displayName}</h3>
            <button className="staff-secondary-button focus-ring" type="button" onClick={() => { setEmailForm(null); }}>{language === 'en' ? 'Close' : 'Cerrar'}</button>
          </div>
          <p className="staff-account-helper">
            {language === 'en'
              ? 'Add a missing Google email without changing the existing verified binding. Replacing an existing email resets the Google binding, suspends the account, clears MFA evidence, and requires the next verified Google sign-in before activation.'
              : 'Agregue un correo de Google faltante sin cambiar el vinculo verificado existente. Reemplazar un correo existente reinicia el vinculo de Google, suspende la cuenta, borra la evidencia MFA y requiere el proximo inicio verificado antes de activar.'}
          </p>
          <form className="staff-account-form" onSubmit={(event) => { void submitEmailUpdate(event); }}>
            <label>
              <span>{language === 'en' ? 'Google email for sign-in' : 'Correo de Google para iniciar sesion'}</span>
              <input className="focus-ring" type="email" value={emailForm.providerEmail} onChange={(event) => { setEmailForm({ ...emailForm, providerEmail: event.target.value }); }} />
              {emailErrors.providerEmail ? <small role="alert">{emailErrors.providerEmail}</small> : null}
            </label>
            <label>
              <span>{language === 'en' ? 'Reason' : 'Motivo'}</span>
              <textarea className="focus-ring" value={emailForm.reasonText} onChange={(event) => { setEmailForm({ ...emailForm, reasonText: event.target.value }); }} />
              {emailErrors.reasonText ? <small role="alert">{emailErrors.reasonText}</small> : null}
            </label>
            <button className="staff-primary-button focus-ring" type="submit">{language === 'en' ? 'Save Google email' : 'Guardar correo'}</button>
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
          {delegationPanel.loading ? <p>{language === 'en' ? 'Loading' : 'Cargando'}</p> : null}
          {delegationPanel.error ? <p className="staff-account-error" role="alert">{delegationPanel.error}</p> : null}
          <div className="staff-delegation-list" aria-label={language === 'en' ? 'Staff delegations' : 'Delegaciones del personal'}>
            {delegationPanel.items.map((delegation) => (
              <div className="staff-delegation-row" key={delegation.delegationId}>
                <span>
                  <strong>{delegation.permissionName}</strong>
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
                  {permissions.map((permission) => <option key={permission} value={permission}>{permission}</option>)}
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
