import { useEffect, useRef, useState } from 'react';

import { clearStaffIdToken, getJwtExpiration, getStaffAuthConfig, setStaffIdToken, useStaffAuthSession } from './staffAuthSession';
import type { StaffAuthConfig } from './staffAuthSession';
import { useLanguage } from '../i18n/LanguageProvider';

type GoogleCredentialResponse = {
  credential?: string;
};

type GoogleAccountsId = {
  disableAutoSelect: () => void;
  initialize: (config: {
    client_id: string;
    callback: (response: GoogleCredentialResponse) => void;
    auto_select?: boolean;
    essential_claims?: string;
  }) => void;
  renderButton: (parent: HTMLElement, options: { size: 'medium'; theme: 'outline'; text: 'signin_with'; shape: 'rectangular' }) => void;
};

declare global {
  interface Window {
    google?: {
      accounts?: {
        id?: GoogleAccountsId;
      };
    };
  }
}

type GoogleStaffSignInProps = {
  compact?: boolean;
  onSignedIn?: () => void;
};

let scriptPromise: Promise<void> | null = null;

function loadGoogleIdentityScript(): Promise<void> {
  if (window.google?.accounts?.id) return Promise.resolve();
  if (scriptPromise !== null) return scriptPromise;
  scriptPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>('script[data-golden-rose-google-identity]');
    if (existing) {
      existing.addEventListener('load', () => { resolve(); }, { once: true });
      existing.addEventListener('error', () => { reject(new Error('google_identity_load_failed')); }, { once: true });
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.dataset.goldenRoseGoogleIdentity = 'true';
    script.referrerPolicy = 'no-referrer';
    script.addEventListener('load', () => { resolve(); }, { once: true });
    script.addEventListener('error', () => { reject(new Error('google_identity_load_failed')); }, { once: true });
    document.head.append(script);
  });
  return scriptPromise;
}

function statusText(
  state: 'loading' | 'ready' | 'signed_in' | 'synthetic' | 'unsupported' | 'unavailable' | 'failed',
  language: 'en' | 'es',
) {
  const labels = {
    loading: {
      en: 'Checking staff sign-in...',
      es: 'Verificando inicio de sesion del personal...',
    },
    ready: {
      en: 'Sign in with Google to continue.',
      es: 'Inicie sesion con Google para continuar.',
    },
    signed_in: {
      en: 'Google sign-in received. Golden Rose must still verify your account access.',
      es: 'Se recibió el inicio de Google. Golden Rose aún debe verificar su acceso.',
    },
    synthetic: {
      en: 'Local synthetic staff auth is active.',
      es: 'La autenticacion sintetica local esta activa.',
    },
    unsupported: {
      en: 'The configured staff identity provider is not supported by this browser sign-in panel.',
      es: 'El proveedor de identidad configurado no es compatible con este panel.',
    },
    unavailable: {
      en: 'Staff sign-in configuration is unavailable.',
      es: 'La configuracion de inicio de sesion no esta disponible.',
    },
    failed: {
      en: 'Google sign-in could not start. Try reloading this page.',
      es: 'No se pudo iniciar Google. Recargue esta pagina.',
    },
  } as const;
  return labels[state][language];
}

export function GoogleStaffSignIn({ compact = false, onSignedIn }: GoogleStaffSignInProps) {
  const { language } = useLanguage();
  const buttonRef = useRef<HTMLDivElement | null>(null);
  const session = useStaffAuthSession();
  const [config, setConfig] = useState<StaffAuthConfig | null>(null);
  const [state, setState] = useState<'loading' | 'ready' | 'signed_in' | 'synthetic' | 'unsupported' | 'unavailable' | 'failed'>('loading');

  useEffect(() => {
    let cancelled = false;
    void getStaffAuthConfig().then((result) => {
      if (cancelled) return;
      if (!result.ok) {
        setState(result.failure === 'unavailable' ? 'unavailable' : 'failed');
        return;
      }
      setConfig(result.value);
      if (result.value.authMode === 'synthetic') {
        setState('synthetic');
        return;
      }
      if (result.value.provider !== 'google' || result.value.googleClientId === null) {
        setState('unsupported');
        return;
      }
      setState(session.idToken === null ? 'ready' : 'signed_in');
    });
    return () => {
      cancelled = true;
    };
  }, [session.idToken]);

  useEffect(() => {
    const googleClientId = config?.googleClientId;
    if (config?.provider !== 'google' || googleClientId === null || googleClientId === undefined || session.idToken !== null) return;
    let cancelled = false;
    void loadGoogleIdentityScript().then(() => {
      if (cancelled || buttonRef.current === null || !window.google?.accounts?.id) return;
      buttonRef.current.replaceChildren();
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        auto_select: false,
        essential_claims: 'auth_time, amr',
        callback: (response) => {
          if (!response.credential) {
            setState('failed');
            return;
          }
          setStaffIdToken(response.credential, getJwtExpiration(response.credential));
          setState('signed_in');
          onSignedIn?.();
        },
      });
      window.google.accounts.id.renderButton(buttonRef.current, {
        size: 'medium',
        theme: 'outline',
        text: 'signin_with',
        shape: 'rectangular',
      });
    }).catch(() => {
      if (!cancelled) setState('failed');
    });
    return () => {
      cancelled = true;
    };
  }, [config, onSignedIn, session.idToken]);

  if (state === 'synthetic') return null;

  return (
    <section
      aria-label={language === 'en' ? 'Staff Google sign-in' : 'Inicio de sesion de Google para personal'}
      className={compact ? 'staff-google-signin staff-google-signin--compact' : 'staff-google-signin'}
    >
      <p role={state === 'failed' || state === 'unavailable' || state === 'unsupported' ? 'alert' : 'status'}>
        {statusText(state, language)}
      </p>
      {session.idToken === null && state === 'ready' ? <div ref={buttonRef} className="staff-google-signin__button" /> : null}
      {session.idToken !== null ? (
        <button
          className="staff-secondary-button focus-ring"
          type="button"
          onClick={() => {
            window.google?.accounts?.id?.disableAutoSelect();
            clearStaffIdToken();
          }}
        >
          {language === 'en' ? 'Clear Golden Rose session' : 'Borrar sesion de Golden Rose'}
        </button>
      ) : null}
    </section>
  );
}
