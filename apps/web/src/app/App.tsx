import { BrowserRouter, Navigate, Route, Routes } from 'react-router';

import { AppShell } from './AppShell';
import { NotFoundPage } from './NotFoundPage';
import { EmployerWorkspace } from '../employers/EmployerWorkspace';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<Navigate to="/employers" replace />} />
        <Route path="employers" element={<EmployerWorkspace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
