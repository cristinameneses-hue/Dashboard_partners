import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { PARTNER_CATEGORIES } from '../types';
import LudaLogo from './LudaLogo';

interface LayoutProps {
  children: ReactNode;
}

const navItems = [
  { path: '/', label: 'Ecommerce', icon: '📊', description: 'Métricas de partners' },
  { path: '/shortage', label: 'Shortage', icon: '🔄', description: 'Transferencias internas' },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 fixed h-full sidebar shadow-xl">
        {/* Logo */}
        <div className="p-6">
          <Link to="/" className="flex items-center gap-3">
            <LudaLogo size={48} />
            <div>
              <h1 className="font-bold text-xl text-white">LUDA</h1>
              <p className="text-xs text-white/70">Partners Dashboard</p>
            </div>
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
                className={`sidebar-link ${isActive ? 'active' : ''}`}
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

        {/* Categories */}
        <div className="px-4 mt-6">
          <p className="text-xs font-medium text-white/50 uppercase tracking-wider px-4 mb-3">
            Categorías
          </p>
          <div className="space-y-1 max-h-64 overflow-y-auto">
            {PARTNER_CATEGORIES.filter(cat => cat.id !== 'all').map((category) => (
              <div key={category.id} className="px-4 py-2">
                <div className="flex items-center gap-2 mb-1">
                  <div 
                    className="w-2.5 h-2.5 rounded-full border-2 border-white/30"
                    style={{ backgroundColor: category.color }}
                  />
                  <span className="text-sm font-medium text-white/90">
                    {category.name}
                  </span>
                </div>
                <div className="ml-5 space-y-0.5">
                  {category.partners.map((partner) => (
                    <div key={partner} className="text-xs text-white/50 capitalize">
                      {partner.replace('-', ' ')}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-4">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                <span className="text-white text-sm">🔗</span>
              </div>
              <div>
                <p className="text-xs text-white/50">Conectado a</p>
                <p className="text-sm font-medium text-white">LudaFarma-PRO</p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64">
        {/* Top Bar */}
        <header className="bg-white shadow-sm border-b border-gray-200 px-8 py-4 sticky top-0 z-40">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-800">
                {location.pathname === '/' ? 'Ecommerce Dashboard' : 'Shortage Dashboard'}
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
