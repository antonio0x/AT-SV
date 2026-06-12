# Spec: improve-tax-assistant — PR #1 (Bug Fixes + De-hardcoding)

## 1. Validation Bug — Aceptar "0" como input válido

### Current
```jsx
disabled={!income || !expenses || !socialContribution}
```
Esto da `true` cuando el valor es `"0"` (falsy string), bloqueando el botón.

### Expected
El botón se habilita siempre que los campos tengan un valor numérico (incluyendo `0`).
Validación: `value === ''` en vez de `!value`.
Para campos opcionales (dependientes), usar `value === ''` como indicador de no-set.

### Files
- `src/calculator/ISRCalculator.jsx`
- `src/calculator/IVACalculator.jsx`
- `src/calculator/ISCCalculator.jsx`
- `src/calculator/PatrimonioCalculator.jsx`

---

## 2. NaN en previsualización ISRCalculator

### Current
```jsx
const taxableIncome = parseFloat(income) - parseFloat(expenses) - ...
```
Si `income` está vacío, `parseFloat('')` → `NaN`. `displayTaxable` muestra `NaN`.

### Expected
`displayTaxable` y `taxResult` muestran `"0.00"` cuando algún campo está vacío.
Usar `Number(value) || 0` o guard clause.

### Files
- `src/calculator/ISRCalculator.jsx`

---

## 3. CSS — Selector global `a` rompe links

### Current
```css
a { @apply text-green-600 hover:text-red-700 underline; }
```
Todos los links del sitio se ven verdes con hover rojo.

### Expected
Links de navegación sin estilo directo (heredan del componente).
Links de texto: `text-blue-600 hover:text-blue-700 underline`.
No usar selector global `a` — aplicar clases directamente en los links.

### Files
- `src/index.css`

---

## 4. Header — Nav activo inconsistente

### Current
```jsx
isActive ? "bg-blue-100 text-green-700" : ...
```

### Expected
```jsx
isActive ? "bg-blue-100 text-blue-700" : ...
```

### Files
- `src/components/layout/Header.jsx`

---

## 5-8. Extraer tasas/tramos a config centralizada

### Current
Cada calculadora define tasas adentro del componente:
- ISR: 3 brackets, 4 tasas
- IVA: 13%
- ISC: 5 categorías
- Patrimonio: 1%

### Expected
Crear `src/data/taxRates.js` con:

```js
export const ISR_RATES = {
  brackets: [
    { min: 0, max: 4064.00, rate: 0 },
    { min: 4064.01, max: 9142.86, rate: 0.10 },
    { min: 9142.87, max: 22857.14, rate: 0.20 },
    { min: 22857.15, max: Infinity, rate: 0.30 },
  ],
  dependentDeduction: 800,
};

export const IVA_RATE = 0.13;

export const ISC_RATES = {
  tobacco: { name: 'Tabaco', rate: 1.00 },
  alcohol: { name: 'Bebidas Alcohólicas', rate: 0.50 },
  softdrinks: { name: 'Bebidas Gaseosas', rate: 0.20 },
  fuels: { name: 'Combustibles', rate: 0.10 },
  others: { name: 'Otros', rate: 0.05 },
};

export const PATRIMONIO_RATE = 0.01;
```

Cada calculadora importa estas constantes en vez de hardcodear.

### Files
- **Nuevo**: `src/data/taxRates.js`
- Modificados: `ISRCalculator.jsx`, `IVACalculator.jsx`, `ISCCalculator.jsx`, `PatrimonioCalculator.jsx`

---

## 9. Extraer constantes corporativas a config

### Current
Footer y ContactPage tienen email, teléfono, dirección hardcodeados.

### Expected
Crear `src/data/constants.js`:

```js
export const APP = {
  name: 'AT-ESV',
  fullName: 'Asistente Tributario de El Salvador',
  tagline: 'Simplificando tus obligaciones fiscales',
  founded: 2026,
};

export const CONTACT = {
  email: 'info@at-esv.com',
  phone: '+503 2XXX XXXX',
  address: 'San Salvador, El Salvador',
  hours: 'Lunes a viernes: 8:00 AM - 5:00 PM',
  saturdayHours: 'Sábados: 9:00 AM - 1:00 PM',
};

export const LINKS = {
  terms: '#',
  privacy: '#',
  about: '#',
  blog: '#',
};
```

### Files
- **Nuevo**: `src/data/constants.js`
- Modificados: `Footer.jsx`, `ContactPage.jsx`

---

## Escenarios de verificación

### Happy path: todos llenos
- ISR: income=25000, expenses=5000, dependents=2, social=1200 → taxable=17,000 → tax esperado
- IVA: amount=100, exento=false → IVA=13, total=113
- ISC: amount=100, type=tobacco → ISC=100, total=200
- Patrimonio: inmuebles=200000, vehiculos=30000, inversiones=50000, otros=10000, deducciones=40000 → neto=250000 → tax=2500

### Edge case: inputs en 0
- ISR: income=0, expenses=0, dependents=0, social=0 → taxable=0 → tax=0
- IVA: amount=0 → IVA=0, total=0

### Edge case: campos vacíos
- Botón deshabilitado si algún campo requerido está vacío
- No se muestra NaN

### CSS
- Links en ContactPage, Footer, LoginPage son azules, no verdes
- Nav activo en Header es azul
