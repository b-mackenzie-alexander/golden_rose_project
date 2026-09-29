import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router';

import { getStaffSession } from '../api/staffAccountClient';
import type { StaffAccountFailureKind, StaffSession } from '../api/staffAccountClient';
import { IconSymbol } from '../dashboard/artwork';
import { useLanguage } from '../i18n/LanguageProvider';

const statusLabels = {
  active: { en: 'Active', es: 'Activa' },
  suspended: { en: 'Suspended', es: 'Suspendida' },
  deprovisioned: { en: 'Deprovisioned', es: 'Retirada' },
};

const authLabels = {
  synthetic: { en: 'Local synthetic session', es: 'Sesion sintetica local' },
  staff_oidc: { en: 'Staff identity provider session', es: 'Sesion del proveedor de identidad' },
};

const failureLabels: Record<StaffAccountFailureKind, { en: string; es: string }> = {
  sign_in_required: {
    en: 'Sign in with the configured staff identity provider to continue.',
    es: 'Inicie sesion con el proveedor de identidad configurado para continuar.',
  },
  authentication_failed: {
    en: 'The staff session could not be verified. Sign in again through the configured provider.',
    es: 'No se pudo verificar la sesion del personal. Inicie sesion otra vez con el proveedor configurado.',
  },
  account_unavailable: {
    en: 'Your staff account is suspended, deprovisioned, or otherwise unavailable. Ask an authorized manager to review it.',
    es: 'Su cuenta esta suspendida, retirada o no disponible. Pida revision a una persona autorizada.',
  },
  identity_provider_unavailable: {
    en: 'The staff identity provider is temporarily unavailable. Try again after the provider recovers.',
    es: 'El proveedor de identidad no esta disponible temporalmente. Intente cuando se recupere.',
  },
  forbidden: {
    en: 'This staff session does not have permission to view the requested account area.',
    es: 'Esta sesion no tiene permiso para ver esta area de cuentas.',
  },
  unavailable: {
    en: 'The account service is unavailable. Try again after the connection recovers.',
    es: 'El servicio de cuentas no esta disponible. Intente cuando se recupere la conexion.',
  },
  unexpected: {
    en: 'The account response could not be used safely.',
    es: 'La respuesta de cuenta no se pudo usar con seguridad.',
  },
  validation: {
    en: 'The account request could not be validated.',
    es: 'No se pudo validar la solicitud de cuenta.',
  },
  not_found: {
    en: 'The account is no longer available.',
    es: 'La cuenta ya no esta disponible.',
  },
  stale: {
    en: 'The account changed in another session. Reload before continuing.',
    es: 'La cuenta cambio en otra sesion. Recargue antes de continuar.',
  },
  unknown_outcome: {
    en: 'The outcome is unknown. Reload before taking another account action.',
    es: 'El resultado es desconocido. Recargue antes de otra accion.',
  },
};

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

function failureText(kind: StaffAccountFailureKind, language: 'en' | 'es') {
  return failureLabels[kind][language];
}

export function StaffAccountProfile() {
  const { language } = useLanguage();
  const [session, setSession] = useState<StaffSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [failure, setFailure] = useState<StaffAccountFailureKind | null>(null);
  const [checkedAt, setCheckedAt] = useState(0);
  const activeDelegations = useMemo(
    () => session?.delegations.filter((item) => item.revokedAt === null && Date.parse(item.expiresAt) > checkedAt) ?? [],
    [checkedAt, session],
  );

  async function reload() {
    setLoading(true);
    setFailure(null);
    const result = await getStaffSession();
    if (result.ok) {
      setSession(result.value);
    } else {
      setSession(null);
      setFailure(result.failure.kind);
    }
    setCheckedAt(Date.now());
    setLoading(false);
  }

  useEffect(() => {
    let cancelled = false;
    void getStaffSession().then((result) => {
      if (cancelled) return;
      if (result.ok) {
        setSession(result.value);
        setFailure(null);
      } else {
        setSession(null);
        setFailure(result.failure.kind);
      }
      setCheckedAt(Date.now());
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const account = session?.account ?? null;
  const displayName = account?.displayName ?? (language === 'en' ? 'Staff session' : 'Sesion del personal');

  return (
    <section aria-labelledby="staff-profile-heading" className="staff-account-page staff-profile-page">
      <div className="staff-account-header">
        <div>
          <p className="module-preview-eyebrow">{language === 'en' ? 'Personal account' : 'Cuenta personal'}</p>
          <h2 id="staff-profile-heading">{language === 'en' ? 'My staff account' : 'Mi cuenta del personal'}</h2>
        </div>
        <button className="staff-secondary-button focus-ring" type="button" onClick={() => { void reload(); }}>
          {language === 'en' ? 'Reload status' : 'Recargar estado'}
        </button>
      </div>

      {loading ? <p role="status">{language === 'en' ? 'Checking staff session...' : 'Verificando sesion del personal...'}</p> : null}
      {failure ? <p className="staff-account-error" role="alert">{failureText(failure, language)}</p> : null}

      {session ? (
        <>
          <div className="staff-profile-summary" aria-label={language === 'en' ? 'Current staff session summary' : 'Resumen de sesion'}>
            <section className="staff-account-panel">
              <h3><IconSymbol name="workers" /> {displayName}</h3>
              <dl className="staff-profile-facts">
                <div>
                  <dt>{language === 'en' ? 'Session type' : 'Tipo de sesion'}</dt>
                  <dd>{authLabels[session.authContext][language]}</dd>
                </div>
                <div>
                  <dt>{language === 'en' ? 'Actor ID' : 'ID de actor'}</dt>
                  <dd>{session.actorId}</dd>
                </div>
                <div>
                  <dt>{language === 'en' ? 'Role' : 'Rol'}</dt>
                  <dd>{account?.roleName ?? session.roleName}</dd>
                </div>
                <div>
                  <dt>{language === 'en' ? 'Lifecycle state' : 'Estado'}</dt>
                  <dd>{account ? statusLabels[account.lifecycleStatus][language] : language === 'en' ? 'No durable account in this environment' : 'Sin cuenta durable en este entorno'}</dd>
                </div>
                <div>
                  <dt>{language === 'en' ? 'MFA evidence' : 'Evidencia MFA'}</dt>
                  <dd>{account?.mfaEnrolled ? 'MFA' : language === 'en' ? 'Not recorded in Golden Rose' : 'No registrada en Golden Rose'}</dd>
                </div>
              </dl>
            </section>

            <section className="staff-account-panel">
              <h3><IconSymbol name="check" /> {language === 'en' ? 'Account boundary' : 'Limite de cuenta'}</h3>
              <p>
                {account
                  ? language === 'en'
                    ? 'This page reflects Golden Rose account evidence and permissions. Provider-side factor resets and session revocation remain outside this application.'
                    : 'Esta pagina refleja evidencia y permisos en Golden Rose. Restablecer factores o revocar sesiones en el proveedor queda fuera de esta aplicacion.'
                  : language === 'en'
                    ? 'This local session is synthetic for development and testing. It is not a production personal account.'
                    : 'Esta sesion local es sintetica para desarrollo y pruebas. No es una cuenta personal de produccion.'}
              </p>
              <Link className="staff-secondary-button focus-ring" to="/staff/admin/accounts">
                {language === 'en' ? 'Open account administration' : 'Abrir administracion de cuentas'}
              </Link>
            </section>
          </div>

          <div className="staff-account-layout">
            <section className="staff-account-panel">
              <h3>{language === 'en' ? 'Active permissions' : 'Permisos activos'}</h3>
              <ul className="staff-profile-list">
                {session.permissionNames.map((permission) => <li key={permission}>{permission}</li>)}
              </ul>
            </section>

            <section className="staff-account-panel">
              <h3>{language === 'en' ? 'Temporary delegations' : 'Delegaciones temporales'}</h3>
              {activeDelegations.length > 0 ? (
                <ul className="staff-profile-list">
                  {activeDelegations.map((delegation) => (
                    <li key={delegation.delegationId}>
                      <strong>{delegation.permissionName}</strong>
                      <span>{language === 'en' ? 'Expires' : 'Vence'} <time dateTime={delegation.expiresAt}>{formatDate(delegation.expiresAt)}</time></span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="staff-account-empty">{language === 'en' ? 'No active temporary delegations.' : 'No hay delegaciones temporales activas.'}</p>
              )}
            </section>
          </div>
        </>
      ) : null}
    </section>
  );
}
