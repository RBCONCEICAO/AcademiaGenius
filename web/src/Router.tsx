import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { Home } from './pages/Home';
import { Settings } from './pages/Settings';
import { Projects } from './pages/Projects';
import { Notebook } from './pages/Notebook';

const router = createBrowserRouter([
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
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);

export function Router() {
  return <RouterProvider router={router} />;
}
