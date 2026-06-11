import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import HomePage from './pages/HomePage';
import CalculatorPage from './pages/CalculatorPage';
import ContactPage from './pages/ContactPage';
import LoginPage from './pages/LoginPage';
import DocumentosPage from './pages/DocumentosPage';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/calculadora" element={<CalculatorPage />} />
          <Route path="/contacto" element={<ContactPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/documentos" element={<DocumentosPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;