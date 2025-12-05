import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { PARTNER_CATEGORIES } from '../types';

interface LayoutProps {
  children: ReactNode;
}

const navItems = [
  { path: '/', label: 'Ecommerce', icon: '◉', description: 'Métricas de partners' },
  { path: '/shortage', label: 'Shortage', icon: '⇄', description: 'Transferencias internas' },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside 
        className="w-64 backdrop-blur-lg border-r border-white/5 fixed h-full overflow-y-auto"
        style={{ backgroundColor: 'rgba(15, 23, 42, 0.5)' }}
      >
        <div className="p-6">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500 to-amber-500 flex items-center justify-center">
              <span className="text-xl font-bold text-white">L</span>
            </div>
            <div>
              <h1 className="font-bold text-xl text-white">LudaFarma</h1>
              <p className="text-xs text-slate-400">Partners Dashboard</p>
            </div>
          </Link>
        </div>

        <nav className="mt-6 px-4">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider px-4 mb-3">
            Analytics
          </p>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl mb-2 transition-all duration-200 ${
                  isActive
                    ? 'bg-sky-600/20 text-sky-400 border border-sky-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <span className="text-lg">{item.icon}</span>
                <div>
                  <span className="font-medium block">{item.label}</span>
                  <span className="text-xs text-slate-500">{item.description}</span>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Categories */}
        <div className="px-4 mt-6">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider px-4 mb-3">
            Categorías
          </p>
          <div className="space-y-1">
            {PARTNER_CATEGORIES.filter(cat => cat.id !== 'all').map((category) => (
              <div key={category.id} className="px-4 py-2">
                <div className="flex items-center gap-2 mb-1">
                  <div 
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: category.color }}
                  />
                  <span className="text-xs font-medium" style={{ color: category.color }}>
                    {category.name}
                  </span>
                </div>
                <div className="ml-4 space-y-0.5">
                  {category.partners.map((partner) => (
                    <div key={partner} className="text-xs text-slate-500 capitalize">
                      {partner.replace('-', ' ')}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-slate-900 to-transparent pt-12">
          <div className="card p-4 bg-gradient-to-br from-sky-600/20 to-amber-500/10">
            <p className="text-xs text-slate-400 mb-1">Conectado a</p>
            <p className="text-sm font-medium text-white">LudaFarma-PRO</p>
            <p className="text-xs text-slate-500 mt-1">MongoDB</p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
