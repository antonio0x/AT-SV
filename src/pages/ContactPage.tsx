import { useState, FormEvent, ChangeEvent } from 'react';
import { Mail, Phone, MapPin, Clock, Send, CheckCircle, AlertCircle } from 'lucide-react';
import { CONTACT } from '../data/constants';

const SUBJECTS = [
  { value: '', label: 'Selecciona un asunto' },
  { value: 'consulta', label: 'Consulta tributaria' },
  { value: 'formulario', label: 'Descarga de formulario' },
  { value: 'soporte', label: 'Soporte técnico' },
  { value: 'otro', label: 'Otro' },
];

interface FormData {
  name: string;
  email: string;
  phone: string;
  subject: string;
  message: string;
}

interface FormErrors {
  [key: string]: string;
}

type FormStatus = 'idle' | 'submitting' | 'success' | 'error';

const INITIAL_FORM: FormData = {
  name: '',
  email: '',
  phone: '',
  subject: '',
  message: '',
};

const COLOR_CLASSES: Record<string, string> = {
  blue: 'from-blue-500 to-blue-600',
  emerald: 'from-emerald-500 to-teal-600',
  violet: 'from-violet-500 to-purple-600',
};

export default function ContactPage() {
  const [formData, setFormData] = useState<FormData>(INITIAL_FORM);
  const [errors, setErrors] = useState<FormErrors>({});
  const [status, setStatus] = useState<FormStatus>('idle');

  const handleChange = (field: keyof FormData) => (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, [field]: e.target.value }));
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

    if (!formData.name.trim()) {
      newErrors.name = 'El nombre es obligatorio';
    }
    if (!formData.email.trim()) {
      newErrors.email = 'El correo es obligatorio';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Correo electrónico inválido';
    }
    if (!formData.subject) {
      newErrors.subject = 'Seleccioná un asunto';
    }
    if (!formData.message.trim()) {
      newErrors.message = 'El mensaje es obligatorio';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setStatus('submitting');
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setStatus('success');
      setFormData(INITIAL_FORM);
    } catch {
      setStatus('error');
    }
  };

  if (status === 'success') {
    return (
      <div className="safe-area py-16 md:py-24">
        <div className="max-w-lg mx-auto text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">¡Mensaje enviado!</h1>
          <p className="text-gray-600 mb-8">
            Gracias por contactarnos. Te responderemos en menos de 24 horas hábiles.
          </p>
          <button onClick={() => setStatus('idle')} className="btn-primary">
            Enviar otro mensaje
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="safe-area py-16 md:py-24">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <Mail className="w-16 h-16 text-blue-600 mx-auto mb-4" />
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Contactanos</h1>
          <p className="text-lg text-gray-600">Tenemos un equipo especializado listo para ayudarte con tus preguntas tributarias.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {[
            { icon: Phone, title: 'Teléfono', value: CONTACT.phone, color: 'blue' },
            { icon: Mail, title: 'Correo', value: CONTACT.email, color: 'emerald' },
            { icon: MapPin, title: 'Ubicación', value: CONTACT.address, color: 'violet' },
          ].map((contact, idx) => {
            const Icon = contact.icon;
            return (
              <div key={idx} className="card text-center">
                <div className={`inline-flex p-4 rounded-lg bg-gradient-to-br ${COLOR_CLASSES[contact.color]} mb-4`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-bold text-gray-900 mb-2">{contact.title}</h3>
                <p className="text-gray-600">{contact.value}</p>
              </div>
            );
          })}
        </div>

        <div className="card">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Envíanos un mensaje</h2>
          {status === 'error' && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3" role="alert">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">Hubo un error al enviar tu mensaje. Por favor intentá de nuevo.</p>
            </div>
          )}
          <form className="space-y-6" onSubmit={handleSubmit} noValidate>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">Nombre <span className="text-red-500">*</span></label>
                <input id="name" type="text" className={`input-field ${errors.name ? 'border-red-500 focus:ring-red-500' : ''}`} placeholder="Tu nombre" value={formData.name} onChange={handleChange('name')} aria-invalid={!!errors.name} aria-describedby={errors.name ? 'name-error' : undefined} />
                {errors.name && <p id="name-error" className="mt-1 text-sm text-red-600">{errors.name}</p>}
              </div>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">Correo Electrónico <span className="text-red-500">*</span></label>
                <input id="email" type="email" className={`input-field ${errors.email ? 'border-red-500 focus:ring-red-500' : ''}`} placeholder="tu@email.com" value={formData.email} onChange={handleChange('email')} aria-invalid={!!errors.email} aria-describedby={errors.email ? 'email-error' : undefined} />
                {errors.email && <p id="email-error" className="mt-1 text-sm text-red-600">{errors.email}</p>}
              </div>
            </div>
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">Teléfono</label>
              <input id="phone" type="tel" className="input-field" placeholder="+503 XXXX XXXX" value={formData.phone} onChange={handleChange('phone')} />
            </div>
            <div>
              <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-2">Asunto <span className="text-red-500">*</span></label>
              <select id="subject" className={`input-field ${errors.subject ? 'border-red-500 focus:ring-red-500' : ''}`} value={formData.subject} onChange={handleChange('subject')} aria-invalid={!!errors.subject} aria-describedby={errors.subject ? 'subject-error' : undefined}>
                {SUBJECTS.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
              {errors.subject && <p id="subject-error" className="mt-1 text-sm text-red-600">{errors.subject}</p>}
            </div>
            <div>
              <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-2">Mensaje <span className="text-red-500">*</span></label>
              <textarea id="message" className={`input-field min-h-40 ${errors.message ? 'border-red-500 focus:ring-red-500' : ''}`} placeholder="Contanos cómo podemos ayudarte..." value={formData.message} onChange={handleChange('message')} aria-invalid={!!errors.message} aria-describedby={errors.message ? 'message-error' : undefined} />
              {errors.message && <p id="message-error" className="mt-1 text-sm text-red-600">{errors.message}</p>}
            </div>
            <button type="submit" className="w-full btn-primary inline-flex items-center justify-center gap-2" disabled={status === 'submitting'}>
              {status === 'submitting' ? (
                <><span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" /> Enviando...</>
              ) : (
                <><Send className="w-4 h-4" /> Enviar Mensaje</>
              )}
            </button>
          </form>
        </div>

        <div className="mt-12 bg-blue-50 rounded-2xl p-8 border border-blue-200">
          <div className="flex items-start space-x-4">
            <Clock className="w-8 h-8 text-blue-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-bold text-gray-900 mb-2">Horario de atención</h3>
              <p className="text-gray-700">{CONTACT.hours.weekdays}</p>
              <p className="text-gray-700">{CONTACT.hours.saturday}</p>
              <p className="text-gray-600 text-sm mt-3">{CONTACT.hours.response}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
