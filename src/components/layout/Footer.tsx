import { Mail, MapPin, Phone } from 'lucide-react';
import { APP, CONTACT, LINKS, SOCIAL } from '../../data/constants';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gradient-to-br from-gray-900 to-gray-950 text-white py-16">
      <div className="safe-area">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
          {/* About */}
          <div>
            <h3 className="text-xl font-bold mb-3">{APP.name}</h3>
            <p className="text-gray-400 text-sm leading-relaxed">
              {APP.fullName}. {APP.tagline} con calculadoras precisas y recursos confiables desde {APP.founded}.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-semibold mb-4 text-gray-100">Enlaces Rápidos</h4>
            <ul className="space-y-2 text-sm">
              <li><a href={LINKS.terms} className="text-gray-400 hover:text-white transition-colors no-underline">Términos y condiciones</a></li>
              <li><a href={LINKS.privacy} className="text-gray-400 hover:text-white transition-colors no-underline">Política de privacidad</a></li>
              <li><a href={LINKS.about} className="text-gray-400 hover:text-white transition-colors no-underline">Sobre nosotros</a></li>
              <li><a href={LINKS.blog} className="text-gray-400 hover:text-white transition-colors no-underline">Blog</a></li>
            </ul>
          </div>

          {/* Services */}
          <div>
            <h4 className="font-semibold mb-4 text-gray-100">Nuestros Servicios</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>✓ Calculadora de impuestos</li>
              <li>✓ Descarga de formularios</li>
              <li>✓ Normativa tributaria</li>
              <li>✓ Asesoría fiscal</li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-semibold mb-4 text-gray-100">Contáctanos</h4>
            <div className="space-y-3 text-sm">
              <div className="flex items-start space-x-3">
                <MapPin className="w-5 h-5 mt-0.5 text-blue-400 flex-shrink-0" />
                <span className="text-gray-400">{CONTACT.address}</span>
              </div>
              <div className="flex items-start space-x-3">
                <Phone className="w-5 h-5 mt-0.5 text-blue-400 flex-shrink-0" />
                <span className="text-gray-400">{CONTACT.phone}</span>
              </div>
              <div className="flex items-start space-x-3">
                <Mail className="w-5 h-5 mt-0.5 text-blue-400 flex-shrink-0" />
                <span className="text-gray-400">{CONTACT.email}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Social Links */}
        <div className="border-t border-gray-800 pt-8 flex items-center justify-between">
          <p className="text-sm text-gray-500">© {currentYear} {APP.fullName}. Todos los derechos reservados.</p>
          <div className="flex space-x-4">
            {SOCIAL.map((social, idx) => (
              <a
                key={idx}
                href={social.href}
                className="p-2 rounded-lg bg-gray-800 hover:bg-blue-600 transition-colors"
                aria-label={social.label}
                title={social.label}
              >
                <span className="text-white">{social.icon}</span>
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}