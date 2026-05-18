import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  GraduationCap, Home, FolderOpen, Settings, LogOut,
  BookOpen, Menu, X, ChevronRight,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { signOut } from '../../lib/supabase';

const NAV = [
  { to: '/',         icon: Home,       label: 'Dashboard',    end: true },
  { to: '/projects', icon: FolderOpen, label: 'Meus Projetos', end: false },
  { to: '/notebook', icon: BookOpen,   label: 'Notebook AI',   end: false },
];

export function AppLayout() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await signOut();
    navigate('/login');
  };

  const avatar = user?.user_metadata?.avatar_url;
  const name   = user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'Usuário';

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="h-16 flex items-center px-5 border-b border-white/10 shrink-0">
        <div className="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center mr-2.5">
          <GraduationCap className="w-5 h-5 text-white" />
        </div>
        <span className="text-lg font-bold text-white tracking-tight">AcademiaGenius</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
        {NAV.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to} to={to} end={end}
            onClick={() => setSidebarOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group ${
                isActive
                  ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/25'
                  : 'text-slate-400 hover:text-white hover:bg-white/8'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={`w-4.5 h-4.5 shrink-0 ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-white'}`} />
                <span className="flex-1">{label}</span>
                {isActive && <ChevronRight className="w-3.5 h-3.5 opacity-60" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Settings + User */}
      <div className="px-3 pb-4 space-y-1 shrink-0">
        <NavLink
          to="/settings"
          onClick={() => setSidebarOpen(false)}
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group ${
              isActive ? 'bg-indigo-500 text-white' : 'text-slate-400 hover:text-white hover:bg-white/8'
            }`
          }
        >
          <Settings className="w-4.5 h-4.5 shrink-0" />
          <span>Configurações</span>
        </NavLink>

        {/* User card */}
        <div className="mt-3 pt-3 border-t border-white/10">
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-white/5 border border-white/10">
            {avatar
              ? <img src={avatar} alt={name} className="w-8 h-8 rounded-full object-cover shrink-0" />
              : <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center shrink-0 text-white text-sm font-bold">{name[0].toUpperCase()}</div>
            }
            <div className="flex-1 min-w-0">
              <p className="text-white text-xs font-semibold truncate">{name}</p>
              <p className="text-slate-500 text-xs truncate">{user?.email}</p>
            </div>
            <button onClick={handleLogout} title="Sair"
              className="text-slate-500 hover:text-red-400 transition p-1 rounded-lg hover:bg-red-500/10">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar — desktop */}
      <aside className="hidden md:flex w-60 bg-slate-900 flex-col shrink-0">
        <SidebarContent />
      </aside>

      {/* Mobile overlay sidebar */}
      {sidebarOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
          <aside className="relative w-64 bg-slate-900 flex flex-col z-10">
            <button onClick={() => setSidebarOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white transition">
              <X className="w-5 h-5" />
            </button>
            <SidebarContent />
          </aside>
        </div>
      )}

      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-40 h-14 bg-slate-900 border-b border-white/10 flex items-center px-4 gap-3">
        <button onClick={() => setSidebarOpen(true)} className="text-slate-400 hover:text-white transition">
          <Menu className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-indigo-500 rounded-md flex items-center justify-center">
            <GraduationCap className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="text-white font-bold text-sm">AcademiaGenius</span>
        </div>
      </div>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <div className="md:hidden h-14" />
        <div className="p-6 md:p-8 max-w-6xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
