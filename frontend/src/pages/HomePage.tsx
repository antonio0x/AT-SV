import { Calculator, FileText, MessageSquare, TrendingUp, Users, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function HomePage() {
  const services = [
    {
      title: 'Calculadora de Impuestos',
      description: 'ISR, IVA, ISC y Patrimonio en un solo lugar. Cálculos precisos según la normativa salvadoreña.',
      icon: Calculator,
      color: 'from-blue-500 to-blue-600',
      to: '/calculadora',
    },
    {
      title: 'Descarga de Formularios',
      description: 'Accedé a recursos, guías y formularios oficiales. Todo lo que necesitás está aquí.',
      icon: FileText,
      color: 'from-emerald-500 to-teal-600',
      to: '/documentos',
    },
    {
      title: 'Asesoría Fiscal',
      description: 'Resolvé dudas y ordená tus obligaciones tributarias con apoyo especializado.',
      icon: MessageSquare,
      color: 'from-violet-500 to-purple-600',
      to: '/contacto',
    },
  ];

  const features = [
    { text: 'Cálculos precisos según leyes salvadoreñas' },
    { text: 'Interfaz responsiva y amigable' },
    { text: 'Sin comisiones, totalmente gratuito' },
    { text: 'Protección de datos garantizada' },
  ];

  return (
    <div className="w-full">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white py-20 md:py-32">
        <div className="safe-area">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="max-w-2xl">
              <div className="inline-block mb-4 px-4 py-2 rounded-full bg-white/20 backdrop-blur border border-white/30">
                <span className="text-sm font-semibold">✨ Bienvenido al Asistente Tributario</span>
              </div>
              <h1 className="text-5xl sm:text-6xl font-black leading-tight mb-6">
                Simplificá tus obligaciones tributarias
              </h1>
              <p className="text-lg sm:text-xl text-blue-100 mb-8 leading-relaxed">
                Calculá impuestos, descargá formularios y mantenete informado con una experiencia clara, rápida y responsiva. 100% gratuito y confiable.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/calculadora"
                  className="inline-flex items-center justify-center px-8 py-4 rounded-xl bg-white text-blue-700 font-bold hover:bg-blue-50 hover:shadow-xl transition-all duration-200"
                >
                  <Calculator className="w-5 h-5 mr-2" />
                  Ir a la Calculadora
                </Link>
                <Link
                  to="/contacto"
                  className="inline-flex items-center justify-center px-8 py-4 rounded-xl border-2 border-white font-bold hover:bg-white/10 hover:shadow-xl transition-all duration-200"
                >
                  <MessageSquare className="w-5 h-5 mr-2" />
                  Contactanos
                </Link>
              </div>
            </div>

            {/* Hero Image Placeholder */}
            <div className="hidden lg:block">
              <div className="bg-white/10 backdrop-blur rounded-2xl p-8 border border-white/20 hover:border-white/40 transition-all">
                <div className="space-y-4">
                  <div className="bg-white/20 rounded-xl p-4 flex items-center space-x-3">
                    <div className="w-12 h-12 rounded-lg bg-white/30 flex items-center justify-center">
                      <TrendingUp className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-sm text-blue-100">ISR • IVA • ISC • Patrimonio</p>
                      <p className="font-semibold">Todos los impuestos</p>
                    </div>
                  </div>
                  <div className="bg-white/20 rounded-xl p-4 flex items-center space-x-3">
                    <div className="w-12 h-12 rounded-lg bg-white/30 flex items-center justify-center">
                      <CheckCircle className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-sm text-blue-100">Formularios y recursos</p>
                      <p className="font-semibold">Descargas disponibles</p>
                    </div>
                  </div>
                  <div className="bg-white/20 rounded-xl p-4 flex items-center space-x-3">
                    <div className="w-12 h-12 rounded-lg bg-white/30 flex items-center justify-center">
                      <Users className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-sm text-blue-100">Soporte especializado</p>
                      <p className="font-semibold">Siempre disponible</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 md:py-24 bg-white">
        <div className="safe-area">
          <h2 className="text-4xl font-bold text-center mb-16 gradient-text">
            ¿Por qué elegir AT-ESV?
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {features.map((feature, idx) => (
              <div key={idx} className="card text-center hover:shadow-lg transition-shadow">
                <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-3" />
                <p className="font-medium text-gray-800">{feature.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-16 md:py-24 bg-gray-50">
        <div className="safe-area">
          <h2 className="text-4xl font-bold text-center mb-3 text-gray-900">
            Nuestros Servicios
          </h2>
          <p className="text-center text-gray-600 text-lg mb-16 max-w-2xl mx-auto">
            Herramientas completas para simplificar tu gestión tributaria en El Salvador
          </p>

          <div className="grid md:grid-cols-3 gap-8">
            {services.map((service) => {
              const Icon = service.icon;
              return (
                <Link
                  key={service.title}
                  to={service.to}
                  className="card hover:shadow-xl hover:border-blue-200 group transition-all duration-300 block no-underline"
                >
                  <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${service.color} mb-4`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-3 group-hover:text-blue-600 transition-colors">
                    {service.title}
                  </h3>
                  <p className="text-gray-600 text-sm leading-relaxed">{service.description}</p>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 md:py-24 bg-gradient-to-br from-blue-600 to-indigo-800 text-white">
        <div className="safe-area text-center">
          <h2 className="text-4xl font-bold mb-6">¿Listo para comenzar?</h2>
          <p className="text-lg text-blue-100 mb-8 max-w-2xl mx-auto">
            Accedé a nuestras herramientas tributarias ahora mismo. Es simple, rápido y completamente gratuito.
          </p>
          <Link
            to="/calculadora"
            className="inline-flex items-center px-8 py-4 rounded-xl bg-white text-blue-700 font-bold hover:bg-blue-50 hover:shadow-xl transition-all duration-200"
          >
            <Calculator className="w-5 h-5 mr-2" />
            Ir a la Calculadora
          </Link>
        </div>
      </section>
    </div>
  );
}