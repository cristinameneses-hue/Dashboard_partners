import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import LudaLogo from './LudaLogo';
import LudaLogoFull from './LudaLogoFull';
import { useAuth } from '../contexts/AuthContext';

interface LayoutProps {
  children: ReactNode;
}

const navItems = [
  { path: '/', label: 'Ecommerce', icon: '📊', description: 'Partner metrics' },
  { path: '/shortage', label: 'Shortage', icon: '🔄', description: 'Internal transfers' },
  { path: '/luda-mind', label: 'Luda Mind', icon: '🧠', description: 'AI queries' },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const { user, logout } = useAuth();

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
                Control panel and metrics
              </p>
            </div>
            <div className="flex items-center gap-4">
              {user && (
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-700">{user.name}</p>
                    <p className="text-xs text-gray-400">{user.email}</p>
                  </div>
                  {user.picture && (
                    <img
                      src={user.picture}
                      alt={user.name}
                      className="w-10 h-10 rounded-full border-2 border-purple-200"
                    />
                  )}
                  <button
                    onClick={logout}
                    className="ml-2 px-3 py-1.5 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Log out"
                  >
                    Logout
                  </button>
                </div>
              )}
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
