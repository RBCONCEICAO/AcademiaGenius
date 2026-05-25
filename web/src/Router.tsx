import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { Home } from './pages/Home';
import { Login } from './pages/Login';
import { Settings } from './pages/Settings';
import { Projects } from './pages/Projects';
import { Notebook } from './pages/Notebook';
import { useAuth } from './context/AuthContext';
import { Loader2 } from 'lucide-react';

/** Guard: redireciona para /login se não autenticado */
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
    </div>
  );
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

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
