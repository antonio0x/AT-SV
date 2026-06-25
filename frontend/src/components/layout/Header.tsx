import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Menu,
  X,
  Calculator,
  FileText,
  Users,
  Home,
  LogIn,
  LogOut,
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuthStore();

  const navigation = [
    { name: 'Inicio', href: '/', icon: Home },
    { name: 'Calculadora', href: '/calculadora', icon: Calculator },
    { name: 'Documentos', href: '/documentos', icon: FileText },
    { name: 'Contacto', href: '/contacto', icon: Users },
  ];

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const desktopNavLink = (
    item: { name: string; href: string; icon: any },
    isActive: boolean,
  ) => {
    const Icon = item.icon;
    return (
      <Link
        key={item.name}
        to={item.href}
        className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
          isActive
            ? 'bg-blue-100 text-blue-700 shadow-sm'
            : 'text-gray-600 hover:bg-gray-100 hover:text-blue-700'
        }`}
      >
        <Icon className="w-4 h-4 mr-2" />
        {item.name}
      </Link>
    );
  };

  const mobileNavLink = (
    item: { name: string; href: string; icon: any },
    isActive: boolean,
  ) => {
    const Icon = item.icon;
    return (
      <Link
        key={item.name}
        to={item.href}
        onClick={() => setMobileMenuOpen(false)}
        className={`flex items-center px-4 py-3 rounded-lg text-base font-medium transition-all duration-200 ${
          isActive
            ? 'bg-blue-100 text-blue-700'
            : 'text-gray-600 hover:bg-gray-100 hover:text-blue-700'
        }`}
      >
        <Icon className="w-5 h-5 mr-3" />
        {item.name}
      </Link>
    );
  };

  const displayName = user?.business_name
    ? user.business_name.length > 20
      ? user.business_name.slice(0, 20) + '...'
      : user.business_name
    : '';

  return (
    <header className="bg-white shadow-lg sticky top-0 z-50 border-b border-gray-200">
      <div className="safe-area">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2 group">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center group-hover:shadow-lg transition-shadow">
                <Calculator className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                AT-ESV
              </span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return desktopNavLink(item, isActive);
            })}

            {isAuthenticated ? (
              <div className="flex items-center space-x-2 ml-2 pl-2 border-l border-gray-200">
                <span className="text-sm font-medium text-gray-700 truncate max-w-[140px]">
                  {displayName}
                </span>
                <button
                  onClick={handleLogout}
                  className="flex items-center px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-red-50 hover:text-red-600 transition-all duration-200"
                >
                  <LogOut className="w-4 h-4 mr-1.5" />
                  Cerrar sesión
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  location.pathname === '/login'
                    ? 'bg-blue-100 text-blue-700 shadow-sm'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-blue-700'
                }`}
              >
                <LogIn className="w-4 h-4 mr-2" />
                Iniciar sesión
              </Link>
            )}
          </nav>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 hover:text-blue-700"
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-t border-gray-200 shadow-lg">
          <div className="safe-area px-2 py-3 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return mobileNavLink(item, isActive);
            })}

            {isAuthenticated ? (
              <>
                <div className="px-4 py-2 text-sm font-medium text-gray-500 border-b border-gray-100">
                  {displayName}
                </div>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    handleLogout();
                  }}
                  className="flex items-center w-full px-4 py-3 rounded-lg text-base font-medium text-gray-600 hover:bg-red-50 hover:text-red-600 transition-all duration-200"
                >
                  <LogOut className="w-5 h-5 mr-3" />
                  Cerrar sesión
                </button>
              </>
            ) : (
              <Link
                to="/login"
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center px-4 py-3 rounded-lg text-base font-medium transition-all duration-200 ${
                  location.pathname === '/login'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-blue-700'
                }`}
              >
                <LogIn className="w-5 h-5 mr-3" />
                Iniciar sesión
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
