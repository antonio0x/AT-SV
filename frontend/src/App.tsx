import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import HomePage from './pages/HomePage';
import CalculatorPage from './pages/CalculatorPage';
import ContactPage from './pages/ContactPage';
import LoginPage from './pages/LoginPage';
import DocumentosPage from './pages/DocumentosPage';
import DashboardPage from './pages/DashboardPage';
import DeclaracionesPage from './pages/DeclaracionesPage';
import DeclarationCreatePage from './pages/DeclarationCreatePage';
import DeclarationDetailPage from './pages/DeclarationDetailPage';
import EmployeesPage from './pages/EmployeesPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { useAuthStore } from './store/authStore';

function App() {
  useEffect(() => { useAuthStore.getState().hydrate(); }, []);

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/calculadora" element={<CalculatorPage />} />
          <Route path="/contacto" element={<ContactPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/documentos" element={<DocumentosPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/declaraciones" element={<DeclaracionesPage />} />
            <Route path="/declaraciones/nueva" element={<DeclarationCreatePage />} />
            <Route path="/declaraciones/:id" element={<DeclarationDetailPage />} />
            <Route path="/empleados" element={<EmployeesPage />} />
          </Route>
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
