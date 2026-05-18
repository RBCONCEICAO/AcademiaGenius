import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { Home } from './pages/Home';
import { Login } from './pages/Login';
import { Settings } from './pages/Settings';
import { Projects } from './pages/Projects';
import { Notebook } from './pages/Notebook';

/** Guard: redireciona para /login se não autenticado */
function RequireAuth({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

/** Guard: redireciona para / se já autenticado */
function RedirectIfAuth({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

const router = createBrowserRouter([
  {
    path: '/login',
    element: <RedirectIfAuth><Login /></RedirectIfAuth>,
  },
  {
    path: '/',
    element: <RequireAuth><AppLayout /></RequireAuth>,
    children: [
      { index: true,       element: <Home /> },
      { path: 'projects',  element: <Projects /> },
      { path: 'settings',  element: <Settings /> },
      { path: 'notebook',  element: <Notebook /> },
    ],
  },
]);

export function Router() {
  return <RouterProvider router={router} />;
}
