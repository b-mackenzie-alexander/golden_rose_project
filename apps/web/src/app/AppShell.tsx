import { NavLink, Outlet } from 'react-router';

import { useLanguage } from '../i18n/LanguageProvider';

export function AppShell() {
  const { messages, toggleLanguage, language } = useLanguage();

  return (
    <>
      <header className="app-header" role="banner">
        <div className="app-header__inner">
          <h1 className="app-brand">{messages.shellHeading}</h1>
          <nav aria-label={messages.primaryNavigation} className="primary-navigation">
            <ul>
              <li>
                <NavLink className="focus-ring nav-link control-44" to="/employers">
                  {messages.employersNav}
                </NavLink>
              </li>
              <li>
                <NavLink className="focus-ring nav-link control-44" to="/staff/intakes/workers">
                  {language === 'en' ? 'Worker intakes' : 'Registros de trabajadores'}
                </NavLink>
              </li>
              <li>
                <NavLink className="focus-ring nav-link control-44" to="/staff/intakes/employers">
                  {language === 'en' ? 'Employer intakes' : 'Registros de empleadores'}
                </NavLink>
              </li>
              <li>
                <NavLink className="focus-ring nav-link control-44" to="/staff/work-interests">
                  {language === 'en' ? 'Work-interest catalog' : 'Catálogo de intereses laborales'}
                </NavLink>
              </li>
            </ul>
          </nav>
          <button
            className="focus-ring language-action control-44"
            type="button"
            onClick={toggleLanguage}
          >
            {messages.switchLanguage}
          </button>
        </div>
      </header>
      <main className="app-main" role="main">
        <Outlet />
      </main>
    </>
  );
}
