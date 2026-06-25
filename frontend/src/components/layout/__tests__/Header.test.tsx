import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Header from '../Header';
import { useAuthStore } from '../../../store/authStore';

function renderHeader() {
  return render(
    <MemoryRouter>
      <Header />
    </MemoryRouter>,
  );
}

describe('Header', () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, isAuthenticated: false, isLoading: false });
  });

  it('shows login link when anonymous', () => {
    renderHeader();
    expect(screen.getByText('Iniciar sesión')).toBeDefined();
  });

  it('shows business_name and logout when authenticated', () => {
    useAuthStore.setState({
      user: {
        user_id: '1',
        email: 'a@b.com',
        business_name: 'Mi Empresa S.A. de C.V.',
        business_type: 'persona_juridica',
        regimen_fiscal: 'general',
      },
      isAuthenticated: true,
    });
    renderHeader();
    expect(screen.getByText('Cerrar sesión')).toBeDefined();
    expect(screen.getByText('Mi Empresa S.A. de C...')).toBeDefined();
  });

  it('truncates long business_name', () => {
    useAuthStore.setState({
      user: {
        user_id: '1',
        email: 'a@b.com',
        business_name: 'Una Empresa Con Nombre Muy Largo S.A. de C.V.',
        business_type: 'persona_juridica',
        regimen_fiscal: 'general',
      },
      isAuthenticated: true,
    });
    renderHeader();
    expect(screen.getByText('Una Empresa Con Nomb...')).toBeDefined();
  });

  it('shows public navigation links when not authenticated', () => {
    renderHeader();
    expect(screen.getByText('Inicio')).toBeDefined();
    expect(screen.getByText('Calculadora')).toBeDefined();
    expect(screen.getByText('Contacto')).toBeDefined();
  });

  it('shows auth navigation links when authenticated', () => {
    useAuthStore.setState({
      user: {
        user_id: '1',
        email: 'a@b.com',
        business_name: 'Test',
        business_type: 'persona_natural',
        regimen_fiscal: 'simplificado',
      },
      isAuthenticated: true,
    });
    renderHeader();
    expect(screen.getByText('Dashboard')).toBeDefined();
    expect(screen.getByText('Declaraciones')).toBeDefined();
    expect(screen.getByText('Documentos')).toBeDefined();
    expect(screen.getByText('Empleados')).toBeDefined();
  });
});
