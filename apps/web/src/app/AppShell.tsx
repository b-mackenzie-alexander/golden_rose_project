import { NavLink, Outlet } from 'react-router';

import { useLanguage } from '../i18n/LanguageProvider';

export function AppShell() {
  const { messages, toggleLanguage } = useLanguage();

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
            </ul>
          </nav>
          <button className="focus-ring language-action control-44" type="button" onClick={toggleLanguage}>
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
