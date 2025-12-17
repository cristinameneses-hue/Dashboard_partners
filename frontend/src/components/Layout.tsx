import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import LudaLogo from './LudaLogo';
import LudaLogoFull from './LudaLogoFull';

interface LayoutProps {
  children: ReactNode;
}

const navItems = [
  { path: '/', label: 'Ecommerce', icon: '📊', description: 'Métricas de partners' },
  { path: '/shortage', label: 'Shortage', icon: '🔄', description: 'Transferencias internas' },
  { path: '/luda-mind', label: 'Luda Mind', icon: '🧠', description: 'Consultas IA' },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="h-screen flex bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 fixed h-full sidebar shadow-xl">
        {/* Logo */}
        <div className="p-4 pb-2">
          <Link to="/" className="block">
            <LudaLogoFull height={55} />
          </Link>
        </div>

        {/* Navigation */}
        <nav className="mt-4 px-4">
          <p className="text-xs font-medium text-white/50 uppercase tracking-wider px-4 mb-3">
            Analytics
          </p>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`sidebar-link ${isActive ? 'active' : ''} ${item.path === '/luda-mind' && isActive ? 'luda-mind-active' : ''}`}
              >
                <span className="text-xl">{item.icon}</span>
                <div>
                  <span className="font-medium block">{item.label}</span>
                  <span className="text-xs text-white/50">{item.description}</span>
                </div>
              </Link>
            );
          })}
        </nav>

      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 h-screen overflow-y-auto">
        {/* Top Bar */}
        <header className="bg-white shadow-sm border-b border-gray-200 px-8 py-4 sticky top-0 z-40">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-800">
                {location.pathname === '/' ? 'Ecommerce Dashboard' : location.pathname === '/luda-mind' ? 'Luda Mind' : 'Shortage Dashboard'}
              </h2>
              <p className="text-sm text-gray-500">
                Panel de control y métricas
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-xs text-gray-400">Última actualización</p>
                <p className="text-sm text-gray-600">{new Date().toLocaleString('es-ES')}</p>
              </div>
              <LudaLogo size={40} />
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
