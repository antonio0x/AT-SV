import { useState, FormEvent, ChangeEvent, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, User, Eye, EyeOff, AlertCircle, Loader } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

type Mode = 'login' | 'register';

interface LoginForm {
  email: string;
  password: string;
  rememberMe: boolean;
}

interface RegisterForm {
  email: string;
  password: string;
  business_name: string;
  business_type: string;
  nit: string;
  nrc: string;
  regimen_fiscal: string;
}

interface FormErrors {
  [key: string]: string;
}

type ButtonStatus = 'idle' | 'loading';

const INITIAL_LOGIN: LoginForm = {
  email: '',
  password: '',
  rememberMe: false,
};

const INITIAL_REGISTER: RegisterForm = {
  email: '',
  password: '',
  business_name: '',
  business_type: '',
  nit: '',
  nrc: '',
  regimen_fiscal: '',
};

export default function LoginPage() {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading, error, login, register, clearError } = useAuthStore();

  const [mode, setMode] = useState<Mode>('login');
  const [showPassword, setShowPassword] = useState(false);
  const [loginForm, setLoginForm] = useState<LoginForm>(INITIAL_LOGIN);
  const [registerForm, setRegisterForm] = useState<RegisterForm>(INITIAL_REGISTER);
  const [errors, setErrors] = useState<FormErrors>({});
  const [buttonStatus, setButtonStatus] = useState<ButtonStatus>('idle');

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  useEffect(() => {
    clearError();
    setErrors({});
    setButtonStatus('idle');
  }, [mode, clearError]);

  const handleLoginChange = (field: keyof LoginForm) => (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setLoginForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const handleRegisterChange = (field: keyof RegisterForm) => (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setRegisterForm((prev) => ({ ...prev, [field]: e.target.value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const validateLogin = (): boolean => {
    const newErrors: FormErrors = {};
    if (!loginForm.email.trim()) {
      newErrors.email = 'El correo o usuario es obligatorio';
    }
    if (!loginForm.password) {
      newErrors.password = 'La contraseña es obligatoria';
    } else if (loginForm.password.length < 6) {
      newErrors.password = 'La contraseña debe tener al menos 6 caracteres';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateRegister = (): boolean => {
    const newErrors: FormErrors = {};

    if (!registerForm.email.trim()) {
      newErrors.email = 'El correo es obligatorio';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.email)) {
      newErrors.email = 'Ingresá un correo válido';
    }

    if (!registerForm.password) {
      newErrors.password = 'La contraseña es obligatoria';
    } else if (registerForm.password.length < 8) {
      newErrors.password = 'La contraseña debe tener al menos 8 caracteres';
    }

    if (!registerForm.business_name.trim()) {
      newErrors.business_name = 'El nombre del negocio es obligatorio';
    }

    if (!registerForm.business_type) {
      newErrors.business_type = 'Seleccioná el tipo de persona';
    }

    if (!registerForm.nit.trim()) {
      newErrors.nit = 'El NIT es obligatorio';
    } else if (!/^\d{4}-\d{6}-\d{3}-\d$/.test(registerForm.nit)) {
      newErrors.nit = 'Formato: 0000-000000-000-0';
    }

    if (!registerForm.regimen_fiscal) {
      newErrors.regimen_fiscal = 'Seleccioná el régimen fiscal';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    clearError();

    if (mode === 'login') {
      if (!validateLogin()) return;
      setButtonStatus('loading');
      try {
        await login(loginForm.email, loginForm.password);
        navigate('/', { replace: true });
      } catch {
        setButtonStatus('idle');
      }
    } else {
      if (!validateRegister()) return;
      setButtonStatus('loading');
      try {
        await register(registerForm);
        navigate('/', { replace: true });
      } catch {
        setButtonStatus('idle');
      }
    }
  };

  return (
    <div className="safe-area py-16 md:py-24">
      <div className="max-w-md mx-auto">
        <div className="text-center mb-12">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {mode === 'login' ? 'Ingresá a tu Cuenta' : 'Creá tu Cuenta'}
          </h1>
          <p className="text-gray-600">
            {mode === 'login' ? 'Accedé a tu panel personalizado' : 'Registrate para acceder a todas las herramientas'}
          </p>
        </div>

        <div className="card shadow-lg">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3" role="alert">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-800">
                  {mode === 'login' ? 'Error al iniciar sesión' : 'Error al registrarse'}
                </p>
                <p className="text-sm text-red-600 mt-1">{error}</p>
              </div>
            </div>
          )}

          <form className="space-y-6" onSubmit={handleSubmit} noValidate>
            {mode === 'register' && (
              <>
                <div>
                  <label htmlFor="business_name" className="block text-sm font-medium text-gray-700 mb-2">
                    Nombre del Negocio <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="business_name"
                    type="text"
                    className={`input-field ${errors.business_name ? 'border-red-500 focus:ring-red-500' : ''}`}
                    placeholder="Mi Empresa S.A. de C.V."
                    value={registerForm.business_name}
                    onChange={handleRegisterChange('business_name')}
                    aria-invalid={!!errors.business_name}
                    aria-describedby={errors.business_name ? 'business_name-error' : undefined}
                  />
                  {errors.business_name && <p id="business_name-error" className="mt-1 text-sm text-red-600">{errors.business_name}</p>}
                </div>

                <div>
                  <label htmlFor="business_type" className="block text-sm font-medium text-gray-700 mb-2">
                    Tipo de Persona <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="business_type"
                    className={`input-field ${errors.business_type ? 'border-red-500 focus:ring-red-500' : ''}`}
                    value={registerForm.business_type}
                    onChange={handleRegisterChange('business_type')}
                    aria-invalid={!!errors.business_type}
                    aria-describedby={errors.business_type ? 'business_type-error' : undefined}
                  >
                    <option value="">Seleccioná una opción</option>
                    <option value="persona_natural">Persona Natural</option>
                    <option value="persona_juridica">Persona Jurídica</option>
                  </select>
                  {errors.business_type && <p id="business_type-error" className="mt-1 text-sm text-red-600">{errors.business_type}</p>}
                </div>

                <div>
                  <label htmlFor="nit" className="block text-sm font-medium text-gray-700 mb-2">
                    NIT <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="nit"
                    type="text"
                    className={`input-field ${errors.nit ? 'border-red-500 focus:ring-red-500' : ''}`}
                    placeholder="0614-290798-101-1"
                    value={registerForm.nit}
                    onChange={handleRegisterChange('nit')}
                    aria-invalid={!!errors.nit}
                    aria-describedby={errors.nit ? 'nit-error' : undefined}
                  />
                  {errors.nit && <p id="nit-error" className="mt-1 text-sm text-red-600">{errors.nit}</p>}
                </div>

                <div>
                  <label htmlFor="nrc" className="block text-sm font-medium text-gray-700 mb-2">
                    NRC <span className="text-gray-400">(opcional)</span>
                  </label>
                  <input
                    id="nrc"
                    type="text"
                    className="input-field"
                    placeholder="12345"
                    value={registerForm.nrc}
                    onChange={handleRegisterChange('nrc')}
                  />
                </div>

                <div>
                  <label htmlFor="regimen_fiscal" className="block text-sm font-medium text-gray-700 mb-2">
                    Régimen Fiscal <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="regimen_fiscal"
                    className={`input-field ${errors.regimen_fiscal ? 'border-red-500 focus:ring-red-500' : ''}`}
                    value={registerForm.regimen_fiscal}
                    onChange={handleRegisterChange('regimen_fiscal')}
                    aria-invalid={!!errors.regimen_fiscal}
                    aria-describedby={errors.regimen_fiscal ? 'regimen_fiscal-error' : undefined}
                  >
                    <option value="">Seleccioná una opción</option>
                    <option value="general">General</option>
                    <option value="simplificado">Simplificado</option>
                  </select>
                  {errors.regimen_fiscal && <p id="regimen_fiscal-error" className="mt-1 text-sm text-red-600">{errors.regimen_fiscal}</p>}
                </div>
              </>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                {mode === 'login' ? 'Usuario o Correo' : 'Correo Electrónico'} <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="email"
                  type="text"
                  className={`input-field pl-10 ${errors.email ? 'border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="tu@email.com"
                  value={mode === 'login' ? loginForm.email : registerForm.email}
                  onChange={mode === 'login' ? handleLoginChange('email') : handleRegisterChange('email')}
                  aria-invalid={!!errors.email}
                  aria-describedby={errors.email ? 'email-error' : undefined}
                />
              </div>
              {errors.email && <p id="email-error" className="mt-1 text-sm text-red-600">{errors.email}</p>}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">Contraseña <span className="text-red-500">*</span></label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  className={`input-field pl-10 pr-10 ${errors.password ? 'border-red-500 focus:ring-red-500' : ''}`}
                  placeholder="••••••••"
                  value={mode === 'login' ? loginForm.password : registerForm.password}
                  onChange={mode === 'login' ? handleLoginChange('password') : handleRegisterChange('password')}
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && <p id="password-error" className="mt-1 text-sm text-red-600">{errors.password}</p>}
            </div>

            {mode === 'login' && (
              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 rounded" checked={loginForm.rememberMe} onChange={handleLoginChange('rememberMe')} />
                  <span className="text-gray-700">Recordarme</span>
                </label>
                <a href="#" className="text-blue-600 hover:text-blue-700 font-medium">¿Olvidaste tu contraseña?</a>
              </div>
            )}

            <button
              type="submit"
              className="w-full btn-primary py-3 inline-flex items-center justify-center gap-2"
              disabled={buttonStatus === 'loading'}
            >
              {buttonStatus === 'loading' ? (
                <><Loader className="w-4 h-4 animate-spin" /> {mode === 'login' ? 'Ingresando...' : 'Registrando...'}</>
              ) : mode === 'login' ? 'Ingresar' : 'Crear Cuenta'}
            </button>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-300" /></div>
              <div className="relative flex justify-center text-sm"><span className="px-2 bg-white text-gray-500">o</span></div>
            </div>

            <button type="button" className="w-full btn-secondary py-3" disabled={buttonStatus === 'loading'}>Continuar con Google</button>
          </form>

          <div className="mt-8 pt-8 border-t border-gray-200 text-center">
            {mode === 'login' ? (
              <p className="text-gray-600">
                ¿No tenés cuenta?{' '}
                <button
                  type="button"
                  onClick={() => setMode('register')}
                  className="text-blue-600 hover:text-blue-700 font-bold inline"
                >
                  Registrate
                </button>
              </p>
            ) : (
              <p className="text-gray-600">
                ¿Ya tenés cuenta?{' '}
                <button
                  type="button"
                  onClick={() => setMode('login')}
                  className="text-blue-600 hover:text-blue-700 font-bold inline"
                >
                  Iniciá sesión
                </button>
              </p>
            )}
          </div>
        </div>

        <p className="text-center text-xs text-gray-500 mt-6">
          Al ingresar, aceptás nuestros{' '}
          <a href="#" className="underline hover:text-gray-700">términos y condiciones</a>{' '}y{' '}
          <a href="#" className="underline hover:text-gray-700">política de privacidad</a>
        </p>
      </div>
    </div>
  );
}
