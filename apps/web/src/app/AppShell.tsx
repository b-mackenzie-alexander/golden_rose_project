import { useEffect, useMemo, useState } from 'react';
import type { SyntheticEvent } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router';

import { BrandRose, IconSymbol } from '../dashboard/artwork';
import type { IconName } from '../dashboard/artwork';
import { queryIntakes } from '../api/intakeClient';
import type { DraftObject, IntakeKind, IntakeSummary } from '../api/intakeContracts';
import { clearStaffIdToken, useStaffAuthSession } from '../auth/staffAuthSession';
import { useLanguage } from '../i18n/LanguageProvider';

type ThemeMode = 'dark' | 'light';

type SearchItem = {
  href: string;
  icon: IconName;
  keywords: string;
  label: string;
  meta: string;
};

type DataSearchItem = SearchItem & {
  id: string;
};

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function intakeSearchHref(kind: IntakeKind, item: IntakeSummary) {
  return `/staff/intakes/${kind === 'worker' ? 'workers' : 'employers'}?reference=${item.intake_id}&open=match`;
}

function dataSearchItem(kind: IntakeKind, item: IntakeSummary, language: 'en' | 'es'): DataSearchItem {
  const displayName = item.display_name?.trim() || (language === 'en' ? 'Unnamed intake' : 'Registro sin nombre');
  const kindLabel = kind === 'worker'
    ? language === 'en' ? 'Worker intake' : 'Registro de trabajador'
    : language === 'en' ? 'Employer intake' : 'Registro de empleador';
  const reviewLabel = language === 'en' ? 'Draft intake record' : 'Borrador de registro';
  return {
    href: intakeSearchHref(kind, item),
    icon: kind === 'worker' ? 'worker' : 'employerIntake',
    id: `${kind}:${item.intake_id}`,
    keywords: `${displayName} ${item.intake_id} ${kindLabel}`,
    label: displayName,
    meta: `${kindLabel} - ${reviewLabel}`,
  };
}

export function AppShell() {
  const { messages, toggleLanguage, language } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();
  const staffAuthSession = useStaffAuthSession();
  const [theme, setTheme] = useState<ThemeMode>('light');
  const [searchValue, setSearchValue] = useState('');
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [dataSearchItems, setDataSearchItems] = useState<DataSearchItem[]>([]);
  const isDark = theme === 'dark';
  const hasStaffBrowserSession = staffAuthSession.idToken !== null;
  const primaryNavItems = [
    { icon: 'home', label: language === 'en' ? 'Home' : 'Inicio', to: '/' },
    {
      icon: 'worker',
      label: language === 'en' ? 'Worker intakes' : 'Registros de trabajadores',
      to: '/staff/intakes/workers',
    },
    { icon: 'building', label: messages.employersNav, to: '/employers' },
    {
      icon: 'employerIntake',
      label: language === 'en' ? 'Employer intakes' : 'Registros de empleadores',
      to: '/staff/intakes/employers',
    },
    {
      icon: 'catalog',
      label: language === 'en' ? 'Work-interest catalog' : 'Catalogo de intereses',
      to: '/staff/work-interests',
    },
    { icon: 'calendar', label: language === 'en' ? 'Calendar' : 'Calendario', to: '/staff/calendar' },
    { icon: 'queue', label: language === 'en' ? 'Work queues' : 'Colas de trabajo', to: '/staff/queues' },
    { icon: 'map', label: language === 'en' ? 'Map' : 'Mapa', to: '/staff/map' },
    { icon: 'reports', label: language === 'en' ? 'Reports' : 'Informes', to: '/staff/reports' },
  ] satisfies Array<{ icon: IconName; label: string; to: string }>;
  const accountNavItems = [
    { icon: 'workers', label: language === 'en' ? 'My account' : 'Mi cuenta', to: '/staff/account' },
    { icon: 'workers', label: language === 'en' ? 'Staff accounts' : 'Cuentas del personal', to: '/staff/admin/accounts' },
  ] satisfies Array<{ icon: IconName; label: string; to: string }>;
  const searchItems = useMemo<Array<SearchItem>>(() => [
    {
      href: '/staff/intakes/workers?queue=review',
      icon: 'document',
      keywords: 'review workers worker review queue pending worker drafts review new drafts revisar trabajadores pendientes',
      label: language === 'en' ? 'Review worker drafts' : 'Revisar borradores de trabajadores',
      meta: language === 'en' ? 'Open the worker review queue' : 'Abrir la cola de revision',
    },
    {
      href: '/staff/queues',
      icon: 'warning',
      keywords: 'urgent requests urgent queue priority due today solicitudes urgentes prioridad vence hoy',
      label: language === 'en' ? 'Urgent requests' : 'Solicitudes urgentes',
      meta: language === 'en' ? 'Prioritized work queue' : 'Cola de trabajo priorizado',
    },
    {
      href: '/staff/calendar',
      icon: 'calendar',
      keywords: 'add calendar event day planner personal company schedule agregar evento calendario agenda',
      label: language === 'en' ? 'Add calendar event' : 'Agregar evento al calendario',
      meta: language === 'en' ? 'Open the staff day planner' : 'Abrir el planificador del personal',
    },
    {
      href: '/staff/intakes/employers',
      icon: 'employerIntake',
      keywords: 'new employer intake employer onboarding demand request nuevo empleador registro demanda',
      label: language === 'en' ? 'New employer intake' : 'Nuevo registro de empleador',
      meta: language === 'en' ? 'Start employer onboarding' : 'Iniciar registro de empleador',
    },
    {
      href: '/staff/intakes/workers',
      icon: 'worker',
      keywords: 'new worker intake worker onboarding registration nuevo trabajador registro',
      label: language === 'en' ? 'New worker intake' : 'Nuevo registro de trabajador',
      meta: language === 'en' ? 'Start worker onboarding' : 'Iniciar registro de trabajador',
    },
    {
      href: '/',
      icon: 'home',
      keywords: 'home dashboard summary kpi today priorities inicio panel resumen metricas',
      label: language === 'en' ? 'Dashboard home' : 'Inicio del panel',
      meta: language === 'en' ? 'KPI cards, priorities, and schedule' : 'Metricas, prioridades y agenda',
    },
    {
      href: '/staff/intakes/workers',
      icon: 'worker',
      keywords: 'worker intake maria lopez carlos rojas lucia torres fictional q person trabajador registro',
      label: language === 'en' ? 'Worker intakes' : 'Registros de trabajadores',
      meta: language === 'en' ? 'Drafts, reviews, and worker records' : 'Borradores, revisiones y trabajadores',
    },
    {
      href: '/staff/intakes/employers',
      icon: 'employerIntake',
      keywords: 'employer intake sunshine home care family first caring hands restaurante la esperanza empleador registro',
      label: language === 'en' ? 'Employer intakes' : 'Registros de empleadores',
      meta: language === 'en' ? 'Employer demand and intake drafts' : 'Demandas y borradores de empleadores',
    },
    {
      href: '/employers',
      icon: 'building',
      keywords: 'employers search records clean homes llc restaurante la esperanza employer follow up empleadores buscar',
      label: language === 'en' ? 'Employer records' : 'Registros de empleadores',
      meta: language === 'en' ? 'Search and revise employer records' : 'Buscar y actualizar empleadores',
    },
    {
      href: '/staff/calendar',
      icon: 'calendar',
      keywords: 'calendar schedule interview ana quispe team check in follow up agenda calendario entrevista',
      label: language === 'en' ? 'Calendar' : 'Calendario',
      meta: language === 'en' ? "Today's schedule and interviews" : 'Agenda y entrevistas de hoy',
    },
    {
      href: '/staff/queues',
      icon: 'queue',
      keywords: 'queue priorities urgent requests incomplete pending work queues cola prioridades solicitudes',
      label: language === 'en' ? 'Work queues' : 'Colas de trabajo',
      meta: language === 'en' ? 'Prioritized work and urgent requests' : 'Trabajo priorizado y solicitudes urgentes',
    },
    {
      href: '/staff/work-interests',
      icon: 'catalog',
      keywords: 'catalog work interest skills positions catalogo intereses habilidades puestos',
      label: language === 'en' ? 'Work-interest catalog' : 'Catalogo de intereses',
      meta: language === 'en' ? 'Skills and work-interest labels' : 'Habilidades e intereses laborales',
    },
    {
      href: '/staff/account',
      icon: 'workers',
      keywords: 'my account staff session sign in mfa permissions delegations personal cuenta sesion permisos',
      label: language === 'en' ? 'My staff account' : 'Mi cuenta del personal',
      meta: language === 'en' ? 'Session state, MFA evidence, and permissions' : 'Sesion, MFA y permisos',
    },
    {
      href: '/staff/admin/accounts',
      icon: 'workers',
      keywords: 'staff accounts admin onboarding activation suspension deprovision recovery session personal cuentas administracion activacion suspension',
      label: language === 'en' ? 'Staff accounts' : 'Cuentas del personal',
      meta: language === 'en' ? 'Onboarding, lifecycle, and access evidence' : 'Incorporacion, ciclo y evidencia de acceso',
    },
    {
      href: '/staff/map',
      icon: 'map',
      keywords: 'map areas bronx manhattan queens brooklyn activity zones mapa zonas',
      label: language === 'en' ? 'Activity map' : 'Mapa de actividad',
      meta: language === 'en' ? 'Area activity and service zones' : 'Actividad por zona y servicio',
    },
    {
      href: '/staff/reports',
      icon: 'reports',
      keywords: 'reports analytics activity metrics informes analitica metricas',
      label: language === 'en' ? 'Reports' : 'Informes',
      meta: language === 'en' ? 'Operational reports and metrics' : 'Informes y metricas operativas',
    },
  ], [language]);
  const normalizedSearch = searchValue.trim().toLocaleLowerCase();
  const shortcutResults = normalizedSearch === ''
    ? []
    : searchItems.filter((item) => `${item.label} ${item.meta} ${item.keywords}`.toLocaleLowerCase().includes(normalizedSearch)).slice(0, 5);
  const searchResults = [...dataSearchItems, ...shortcutResults].slice(0, 7);
  const showSearchPanel = isSearchFocused && searchValue.trim().length > 0;

  useEffect(() => {
    const rawQuery = searchValue.trim();
    const isReference = UUID_PATTERN.test(rawQuery);
    if (rawQuery.length < 2 && !isReference) {
      const timeoutId = window.setTimeout(() => {
        setDataSearchItems([]);
      }, 0);
      return () => {
        window.clearTimeout(timeoutId);
      };
    }

    let cancelled = false;
    const filter: DraftObject = isReference ? { reference: rawQuery.toLowerCase() } : { name_query: rawQuery };
    Promise.all([queryIntakes('worker', filter), queryIntakes('employer', filter)])
      .then(([workerResult, employerResult]) => {
        if (cancelled) return;
        const nextItems = [
          ...(workerResult.ok ? workerResult.value.items.map((item) => dataSearchItem('worker', item, language)) : []),
          ...(employerResult.ok ? employerResult.value.items.map((item) => dataSearchItem('employer', item, language)) : []),
        ];
        setDataSearchItems(nextItems.slice(0, 5));
      })
      .catch(() => {
        if (!cancelled) setDataSearchItems([]);
      });

    return () => {
      cancelled = true;
    };
  }, [language, searchValue]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    if (location.pathname !== '/') {
      return undefined;
    }

    let timeoutId: number | undefined;
    try {
      const savedTheme = window.localStorage.getItem('golden-rose-theme');
      if (savedTheme === 'dark' || savedTheme === 'light') {
        timeoutId = window.setTimeout(() => {
          setTheme(savedTheme);
        }, 0);
      }
    } catch {
      // Local storage can be unavailable in hardened browser contexts.
    }

    return () => {
      if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [location.pathname]);

  function navigateToSearchItem(item: SearchItem) {
    setSearchValue('');
    setIsSearchFocused(false);
    void navigate(item.href);
  }

  function handleSearchSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const [firstResult] = searchResults;
    if (firstResult !== undefined) {
      navigateToSearchItem(firstResult);
    }
  }

  function toggleTheme() {
    const nextTheme = isDark ? 'light' : 'dark';
    setTheme(nextTheme);
    try {
      window.localStorage.setItem('golden-rose-theme', nextTheme);
    } catch {
      // Theme persistence is optional; the visible toggle still works.
    }
  }

  function signOutOfGoldenRoseSession() {
    window.google?.accounts?.id?.disableAutoSelect();
    clearStaffIdToken();
    void navigate('/staff/account');
  }

  return (
    <div className="staff-shell">
      <header className="app-header" role="banner">
        <div className="app-header__inner">
          <form
            aria-label={language === 'en' ? 'Global staff search' : 'Busqueda global del personal'}
            className="global-search"
            role="search"
            onSubmit={handleSearchSubmit}
          >
            <span className="sr-only">{language === 'en' ? 'Global search' : 'Busqueda global'}</span>
            <IconSymbol className="global-search__icon" name="search" />
            <input
              aria-label={language === 'en' ? 'Global search' : 'Busqueda global'}
              className="focus-ring"
              placeholder={language === 'en' ? 'Search workers, employers, or intake references...' : 'Buscar trabajadores, empleadores o referencias...'}
              value={searchValue}
              type="search"
              onBlur={() => {
                window.setTimeout(() => {
                  setIsSearchFocused(false);
                }, 120);
              }}
              onChange={(event) => {
                setSearchValue(event.target.value);
              }}
              onFocus={() => {
                setIsSearchFocused(true);
              }}
            />
            {showSearchPanel ? (
              <div className="global-search-results" id="global-search-results">
                {searchResults.length === 0 ? (
                  <p>
                    {language === 'en' ? 'No matching staff records or dashboard areas found.' : 'No se encontraron registros ni areas coincidentes.'}
                  </p>
                ) : (
                  <ol>
                    {searchResults.map((item) => {
                      const itemKey = 'id' in item && typeof item.id === 'string' ? item.id : `${item.href}:${item.label}`;
                      return (
                      <li key={itemKey}>
                        <button
                          className="focus-ring"
                          type="button"
                          onClick={() => {
                            navigateToSearchItem(item);
                          }}
                        >
                          <span aria-hidden="true" className="search-result-icon"><IconSymbol name={item.icon} /></span>
                          <span>
                            <strong>{item.label}</strong>
                            <small>{item.meta}</small>
                          </span>
                        </button>
                      </li>
                      );
                    })}
                  </ol>
                )}
              </div>
            ) : null}
          </form>
          <div className="header-utility">
            <div className="language-segment" aria-label={language === 'en' ? 'Language' : 'Idioma'}>
              <button
                aria-label={language === 'en' ? messages.switchLanguage : 'Idioma actual: espanol'}
                aria-pressed={language === 'es'}
                className="focus-ring language-action"
                type="button"
                onClick={language === 'en' ? toggleLanguage : undefined}
              >
                Espanol
              </button>
              <button
                aria-label={language === 'es' ? messages.switchLanguage : 'Current language: English'}
                aria-pressed={language === 'en'}
                className="focus-ring language-action"
                type="button"
                onClick={language === 'es' ? toggleLanguage : undefined}
              >
                English
              </button>
            </div>
            <button
              aria-label={isDark
                ? language === 'en' ? 'Switch to light mode' : 'Cambiar a modo claro'
                : language === 'en' ? 'Switch to dark mode' : 'Cambiar a modo oscuro'}
              aria-pressed={isDark}
              className="theme-toggle focus-ring"
              data-enabled={isDark}
              type="button"
              onClick={() => {
                toggleTheme();
              }}
            >
              <IconSymbol name="sun" />
              <span aria-hidden="true" className="theme-toggle__track"><span /></span>
              <IconSymbol name="moon" />
            </button>
            <button aria-label={language === 'en' ? 'Notifications: 3 unread' : 'Notificaciones: 3 sin leer'} className="icon-action focus-ring" type="button">
              <IconSymbol name="bell" />
              <span className="notification-badge">3</span>
            </button>
            {hasStaffBrowserSession ? (
              <button
                aria-label={language === 'en' ? 'Sign out of Golden Rose session' : 'Cerrar sesion de Golden Rose'}
                className="header-signout focus-ring"
                title={language === 'en'
                  ? 'Clears this browser session for Golden Rose. Google may still be signed in.'
                  : 'Borra esta sesion de Golden Rose en el navegador. Google puede seguir activo.'}
                type="button"
                onClick={signOutOfGoldenRoseSession}
              >
                {language === 'en' ? 'Sign out' : 'Cerrar sesion'}
              </button>
            ) : null}
            <button
              aria-label={language === 'en' ? 'Open my staff account' : 'Abrir mi cuenta del personal'}
              className="user-menu focus-ring"
              type="button"
              onClick={() => { void navigate('/staff/account'); }}
            >
              <span className="user-avatar" aria-hidden="true">GR</span>
              <span>
                <strong>{language === 'en' ? 'Staff account' : 'Cuenta del personal'}</strong>
                <small>{language === 'en' ? 'Verify session' : 'Verificar sesion'}</small>
              </span>
            </button>
          </div>
        </div>
      </header>

      <aside className="sidebar" aria-label={messages.primaryNavigation}>
        <div className="sidebar__brand">
          <span className="brand-mark" aria-hidden="true"><BrandRose /></span>
          <h1 aria-label={messages.shellHeading} className="app-brand">
            <span>Nuestro</span>
            {' '}
            <span>Corazón Dorado</span>
          </h1>
          <p>{language === 'en' ? 'People. Opportunities. A Brighter Tomorrow.' : 'Operaciones de Golden Rose'}</p>
        </div>
        <nav aria-label={messages.primaryNavigation} className="primary-navigation">
          <ul>
            {primaryNavItems.map((item) => (
              <li key={item.to}>
                <NavLink className="focus-ring nav-link control-44" to={item.to}>
                  <span aria-hidden="true" className="nav-link__icon"><IconSymbol name={item.icon} /></span>
                  <span>{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
          <ul className="nav-account-group">
            {accountNavItems.map((item) => (
              <li key={item.to}>
                <NavLink className="focus-ring nav-link control-44" to={item.to}>
                  <span aria-hidden="true" className="nav-link__icon"><IconSymbol name={item.icon} /></span>
                  <span>{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <div className="sidebar__footer">
          <div className="sidebar-motto">
            <span aria-hidden="true"><BrandRose /></span>
            <p>{language === 'en' ? 'Strong people. Stronger communities.' : 'Personas fuertes. Comunidades mas fuertes.'}</p>
          </div>
          <p className="sidebar-version">Version 1.0.0</p>
        </div>
      </aside>
      <main className="app-main" role="main">
        <Outlet />
      </main>
    </div>
  );
}
