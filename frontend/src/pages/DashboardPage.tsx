import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LayoutDashboard, FileText, TrendingUp, DollarSign, ClipboardList } from 'lucide-react';
import { Card, Button, Badge } from '../components/ui';
import { useDeclarationStore } from '../store/declarationStore';
import api from '../lib/api';

interface ProjectionData {
  iva_projection?: number;
  pago_cuenta_projection?: number;
  period?: string;
  year?: number;
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const { declarations, fetch } = useDeclarationStore();
  const [projection, setProjection] = useState<ProjectionData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await fetch();
      try {
        const res = await api.get('/taxes/projection');
        setProjection(res.data.data ?? res.data);
      } catch {
        // projection may not be available in all environments
      }
      setLoading(false);
    };
    load();
  }, [fetch]);

  const currentPeriod = `${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`;
  const draftCount = declarations.filter((d) => d.status === 'draft').length;
  const submittedCount = declarations.filter((d) => d.status === 'submitted').length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Período actual: {currentPeriod}</p>
        </div>
        <LayoutDashboard className="w-8 h-8 text-blue-600" />
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <div className="h-24 animate-pulse bg-gray-100 rounded" />
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Proyección IVA</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {projection?.iva_projection != null
                    ? `$${projection.iva_projection.toFixed(2)}`
                    : '—'}
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Proyección Pago a Cuenta</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {projection?.pago_cuenta_projection != null
                    ? `$${projection.pago_cuenta_projection.toFixed(2)}`
                    : '—'}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Declaraciones</p>
                <div className="flex items-center space-x-2 mt-1">
                  <span className="text-2xl font-bold text-gray-900">{declarations.length}</span>
                  <Badge variant="warning">{draftCount} borrador{draftCount !== 1 ? 'es' : ''}</Badge>
                  <Badge variant="success">{submittedCount} presentada{submittedCount !== 1 ? 's' : ''}</Badge>
                </div>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <ClipboardList className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </Card>
        </div>
      )}

      <Card title="Acciones rápidas">
        <div className="flex flex-wrap gap-3">
          <Button onClick={() => navigate('/declaraciones/nueva')}>
            <FileText className="w-4 h-4 mr-2" />
            Nueva declaración IVA
          </Button>
          <Button variant="secondary" onClick={() => navigate('/declaraciones/nueva')}>
            <FileText className="w-4 h-4 mr-2" />
            Nueva declaración Pago a Cuenta
          </Button>
          <Button variant="ghost" onClick={() => navigate('/declaraciones')}>
            <ClipboardList className="w-4 h-4 mr-2" />
            Ver transacciones
          </Button>
        </div>
      </Card>
    </div>
  );
}
