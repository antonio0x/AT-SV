import { useState, ReactNode } from 'react';
import { FileText, Download, Search, FileSpreadsheet, BookOpen, AlertCircle, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { APP } from '../data/constants';

interface Resource {
  id: string;
  name: string;
  description: string;
  category: string;
  format: string;
  available: boolean;
  pages?: number;
}

const RESOURCES: Resource[] = [
  { id: 'isr-guide', name: 'Guía Completa de ISR 2026', description: 'Guía detallada del Impuesto Sobre la Renta para personas naturales y jurídicas.', category: 'ISR', format: 'PDF', available: true, pages: 45 },
  { id: 'form-1000', name: 'Formulario 1000 — ISR Persona Natural', description: 'Declaración anual de ISR para personas naturales.', category: 'ISR', format: 'PDF', available: true },
  { id: 'form-2000', name: 'Formulario 2000 — ISR Persona Jurídica', description: 'Declaración anual de ISR para personas jurídicas.', category: 'ISR', format: 'PDF', available: true },
  { id: 'iva-guide', name: 'Guía de IVA 2026', description: 'Todo sobre el Impuesto al Valor Agregado: tasas, exenciones y declaraciones.', category: 'IVA', format: 'PDF', available: true, pages: 32 },
  { id: 'form-3000', name: 'Formulario 3000 — Declaración IVA', description: 'Declaración mensual del Impuesto al Valor Agregado.', category: 'IVA', format: 'PDF', available: true },
  { id: 'iva-rate-table', name: 'Tabla de Tasas IVA por Producto', description: 'Clasificación de productos y servicios con sus respectivas tasas de IVA.', category: 'IVA', format: 'XLS', available: false },
  { id: 'isc-guide', name: 'Guía de ISC por Producto', description: 'Clasificación de productos sujetos al Impuesto Selectivo al Consumo con sus tasas.', category: 'ISC', format: 'PDF', available: true, pages: 28 },
  { id: 'patrimonio-guide', name: 'Guía de Impuesto al Patrimonio', description: 'Cómo calcular y declarar el Impuesto al Patrimonio, incluyendo deducciones permitidas.', category: 'Patrimonio', format: 'PDF', available: true, pages: 20 },
  { id: 'tax-calendar', name: 'Calendario Tributario 2026', description: 'Fechas clave de vencimientos, declaraciones y pagos de impuestos.', category: 'General', format: 'PDF', available: true, pages: 12 },
  { id: 'faq-guide', name: 'Preguntas Frecuentes Tributarias', description: 'Respuestas a las consultas más comunes sobre obligaciones fiscales en El Salvador.', category: 'General', format: 'PDF', available: true, pages: 18 },
];

interface Category {
  key: string;
  label: string;
  color: string;
}

const CATEGORIES: Category[] = [
  { key: 'all', label: 'Todos', color: 'blue' },
  { key: 'ISR', label: 'ISR', color: 'emerald' },
  { key: 'IVA', label: 'IVA', color: 'violet' },
  { key: 'ISC', label: 'ISC', color: 'amber' },
  { key: 'Patrimonio', label: 'Patrimonio', color: 'rose' },
  { key: 'General', label: 'General', color: 'gray' },
];

const FORMAT_ICONS: Record<string, ReactNode> = {
  PDF: <FileText className="w-3.5 h-3.5" />,
  XLS: <FileSpreadsheet className="w-3.5 h-3.5" />,
};

const CATEGORY_COLORS: Record<string, { bg: string; text: string; badge: string }> = {
  ISR: { bg: 'bg-emerald-100', text: 'text-emerald-700', badge: 'bg-emerald-100 text-emerald-800' },
  IVA: { bg: 'bg-violet-100', text: 'text-violet-700', badge: 'bg-violet-100 text-violet-800' },
  ISC: { bg: 'bg-amber-100', text: 'text-amber-700', badge: 'bg-amber-100 text-amber-800' },
  Patrimonio: { bg: 'bg-rose-100', text: 'text-rose-700', badge: 'bg-rose-100 text-rose-800' },
  General: { bg: 'bg-gray-100', text: 'text-gray-700', badge: 'bg-gray-100 text-gray-800' },
};

export default function DocumentosPage() {
  const [activeCategory, setActiveCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [downloading, setDownloading] = useState<string | null>(null);
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);

  const filtered = RESOURCES.filter((doc) => {
    const matchCategory = activeCategory === 'all' || doc.category === activeCategory;
    const matchSearch =
      searchQuery === '' ||
      doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchCategory && matchSearch;
  });

  const handleDownload = async (docId: string) => {
    setDownloading(docId);
    setDownloadSuccess(null);
    try {
      await new Promise((resolve) => setTimeout(resolve, 1200));
      setDownloading(null);
      setDownloadSuccess(docId);
      setTimeout(() => setDownloadSuccess(null), 3000);
    } catch {
      setDownloading(null);
    }
  };

  const availableCount = RESOURCES.filter((d) => d.available).length;
  const totalCount = RESOURCES.length;

  return (
    <div className="safe-area py-16 md:py-24">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <BookOpen className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-gray-900 mb-4">Centro de Documentos</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">Accedé a guías, formularios y recursos tributarios oficiales preparados por el equipo de {APP.name}.</p>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-10">
          <div className="card text-center py-4">
            <p className="text-3xl font-bold text-blue-600">{availableCount}</p>
            <p className="text-sm text-gray-600 mt-1">Disponibles</p>
          </div>
          <div className="card text-center py-4">
            <p className="text-3xl font-bold text-emerald-600">{totalCount - availableCount}</p>
            <p className="text-sm text-gray-600 mt-1">Próximamente</p>
          </div>
          <div className="card text-center py-4">
            <p className="text-3xl font-bold text-violet-600">{totalCount}</p>
            <p className="text-sm text-gray-600 mt-1">Total Recursos</p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscá documentos, guías o formularios..."
              className="input-field pl-10"
              aria-label="Buscar documentos"
            />
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-8">
          {CATEGORIES.map((cat) => {
            const isActive = activeCategory === cat.key;
            const colors = CATEGORY_COLORS[cat.key === 'all' ? 'General' : cat.key] ?? CATEGORY_COLORS.General;
            return (
              <button
                key={cat.key}
                onClick={() => setActiveCategory(cat.key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive ? `${colors.bg} ${colors.text} shadow-sm` : 'bg-white text-gray-600 border border-gray-200 hover:border-blue-400 hover:text-blue-600'
                }`}
              >
                {cat.label}
              </button>
            );
          })}
        </div>

        <p className="text-sm text-gray-500 mb-4">
          {filtered.length === 0 ? 'No se encontraron documentos con esos filtros.' : `Mostrando ${filtered.length} de ${RESOURCES.length} recursos`}
        </p>

        {filtered.length === 0 ? (
          <div className="card text-center py-16">
            <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-bold text-gray-700 mb-2">Sin resultados</h3>
            <p className="text-gray-500">Probá con otra categoría o término de búsqueda.</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-6 mb-12">
            {filtered.map((doc) => {
              const colors = CATEGORY_COLORS[doc.category] ?? CATEGORY_COLORS.General;
              const isDownloading = downloading === doc.id;
              const isSuccess = downloadSuccess === doc.id;
              const FormatIcon = doc.format === 'XLS' ? FileSpreadsheet : FileText;

              return (
                <article key={doc.id} className={`card hover:shadow-lg transition-all duration-300 ${!doc.available ? 'opacity-60' : 'hover:border-blue-200'}`}>
                  <div className="flex items-start space-x-4">
                    <div className={`w-12 h-12 rounded-lg ${colors.bg} flex items-center justify-center flex-shrink-0`}>
                      <FormatIcon className={`w-6 h-6 ${colors.text}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-bold text-gray-900 truncate">{doc.name}</h3>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors.badge}`}>{doc.category}</span>
                      </div>
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">{doc.description}</p>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3 text-xs text-gray-500">
                          <span className="inline-flex items-center gap-1">
                            {FORMAT_ICONS[doc.format]}
                            {doc.format}
                          </span>
                          {doc.pages && <span>{doc.pages} páginas</span>}
                        </div>
                        {doc.available ? (
                          <button
                            onClick={() => handleDownload(doc.id)}
                            disabled={isDownloading}
                            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
                              isSuccess ? 'bg-green-100 text-green-700' : 'bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50'
                            }`}
                            aria-label={`Descargar ${doc.name}`}
                          >
                            {isDownloading ? (
                              <><span className="animate-spin w-3 h-3 border-2 border-white border-t-transparent rounded-full" /> Descargando...</>
                            ) : isSuccess ? (
                              <><CheckCircle className="w-3.5 h-3.5" /> Descargado</>
                            ) : (
                              <><Download className="w-3.5 h-3.5" /> Descargar</>
                            )}
                          </button>
                        ) : (
                          <span className="px-3 py-1.5 rounded-lg bg-gray-100 text-gray-500 text-xs font-medium">Próximamente</span>
                        )}
                      </div>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}

        <div className="mt-8 bg-gradient-to-br from-gray-900 to-gray-950 text-white rounded-2xl p-8 md:p-12">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div>
              <h3 className="text-2xl font-bold mb-2">¿No encontraste lo que buscabas?</h3>
              <p className="text-gray-400">Contactanos y te asesoramos personalmente sobre los documentos que necesitás.</p>
            </div>
            <Link to="/contacto" className="inline-flex items-center px-6 py-3 rounded-xl bg-blue-600 text-white font-bold hover:bg-blue-700 transition-colors flex-shrink-0">
              Contactar Soporte
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
