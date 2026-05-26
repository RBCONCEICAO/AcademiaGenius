import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { Home } from './pages/Home';
import { Login } from './pages/Login';
import { Settings } from './pages/Settings';
import { Projects } from './pages/Projects';
import { Notebook } from './pages/Notebook';
import { useAuth } from './context/AuthContext';

/** Guard: redireciona para / se já autenticado */
function RedirectIfAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/" replace />;
  return <>{children}</>;
}

const router = createBrowserRouter([
  {
    path: '/login',
    element: <RedirectIfAuth><Login /></RedirectIfAuth>,
  },
  {
    path: '/',
    element: <AppLayout />,
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
