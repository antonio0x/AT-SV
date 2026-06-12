import { useState, FormEvent, ChangeEvent } from 'react';
import { Lock, User, Eye, EyeOff, AlertCircle, CheckCircle, Loader } from 'lucide-react';

interface FormData {
  email: string;
  password: string;
  rememberMe: boolean;
}

interface FormErrors {
  [key: string]: string;
}

type LoginStatus = 'idle' | 'submitting' | 'success' | 'error';

const INITIAL_FORM: FormData = {
  email: '',
  password: '',
  rememberMe: false,
};

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState<FormData>(INITIAL_FORM);
  const [errors, setErrors] = useState<FormErrors>({});
  const [status, setStatus] = useState<LoginStatus>('idle');

  const handleChange = (field: keyof FormData) => (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const validate = (): boolean => {
    const newErrors: FormErrors = {};
    if (!formData.email.trim()) {
      newErrors.email = 'El correo o usuario es obligatorio';
    }
    if (!formData.password) {
      newErrors.password = 'La contraseña es obligatoria';
    } else if (formData.password.length < 6) {
      newErrors.password = 'La contraseña debe tener al menos 6 caracteres';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setStatus('submitting');
    try {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      setStatus('success');
    } catch {
      setStatus('error');
    }
  };

  if (status === 'success') {
    return (
      <div className="safe-area py-16 md:py-24">
        <div className="max-w-md mx-auto text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">¡Inicio de sesión exitoso!</h1>
          <p className="text-gray-600 mb-8">Redirigiendo a tu panel personalizado...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="safe-area py-16 md:py-24">
      <div className="max-w-md mx-auto">
        <div className="text-center mb-12">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Lock className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Ingresá a tu Cuenta</h1>
          <p className="text-gray-600">Accedé a tu panel personalizado</p>
        </div>

        <div className="card shadow-lg">
          {status === 'error' && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3" role="alert">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-800">Error al iniciar sesión</p>
                <p className="text-sm text-red-600 mt-1">Usuario o contraseña incorrectos. Verificá tus credenciales e intentá de nuevo.</p>
              </div>
            </div>
          )}

          <form className="space-y-6" onSubmit={handleSubmit} noValidate>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">Usuario o Correo <span className="text-red-500">*</span></label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input id="email" type="text" className={`input-field pl-10 ${errors.email ? 'border-red-500 focus:ring-red-500' : ''}`} placeholder="tu@email.com" value={formData.email} onChange={handleChange('email')} aria-invalid={!!errors.email} aria-describedby={errors.email ? 'email-error' : undefined} />
              </div>
              {errors.email && <p id="email-error" className="mt-1 text-sm text-red-600">{errors.email}</p>}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">Contraseña <span className="text-red-500">*</span></label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input id="password" type={showPassword ? 'text' : 'password'} className={`input-field pl-10 pr-10 ${errors.password ? 'border-red-500 focus:ring-red-500' : ''}`} placeholder="••••••••" value={formData.password} onChange={handleChange('password')} aria-invalid={!!errors.password} aria-describedby={errors.password ? 'password-error' : undefined} />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600" aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'} tabIndex={-1}>
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && <p id="password-error" className="mt-1 text-sm text-red-600">{errors.password}</p>}
            </div>

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input type="checkbox" className="w-4 h-4 rounded" checked={formData.rememberMe} onChange={handleChange('rememberMe')} />
                <span className="text-gray-700">Recordarme</span>
              </label>
              <a href="#" className="text-blue-600 hover:text-blue-700 font-medium">¿Olvidaste tu contraseña?</a>
            </div>

            <button type="submit" className="w-full btn-primary py-3 inline-flex items-center justify-center gap-2" disabled={status === 'submitting'}>
              {status === 'submitting' ? <><Loader className="w-4 h-4 animate-spin" /> Ingresando...</> : 'Ingresar'}
            </button>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-300" /></div>
              <div className="relative flex justify-center text-sm"><span className="px-2 bg-white text-gray-500">o</span></div>
            </div>

            <button type="button" className="w-full btn-secondary py-3" disabled={status === 'submitting'}>Continuar con Google</button>
          </form>

          <div className="mt-8 pt-8 border-t border-gray-200 text-center">
            <p className="text-gray-600">¿No tenés cuenta?{' '}<a href="#" className="text-blue-600 hover:text-blue-700 font-bold">Registrate ahora</a></p>
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
