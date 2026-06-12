# Design: improve-tax-assistant — PR #1 (Bug Fixes + De-hardcoding)

## Architecture Changes

```
src/
├── data/                  ← NUEVO: config layer
│   ├── taxRates.js        # Tasas y tramos de impuestos
│   └── constants.js       # Constantes corporativas
├── calculator/
│   ├── ISRCalculator.jsx  # Modificado: importa taxRates
│   ├── IVACalculator.jsx  # Modificado: importa taxRates
│   ├── ISCCalculator.jsx  # Modificado: importa taxRates
│   └── PatrimonioCalculator.jsx  # Modificado: importa taxRates
├── components/
│   └── layout/
│       ├── Header.jsx     # Modificado: color nav activo
│       └── Footer.jsx     # Modificado: importa constants
├── pages/
│   └── ContactPage.jsx    # Modificado: importa constants
└── index.css              # Modificado: selector a
```

## Data Layer Design

### `src/data/taxRates.js`

Patrón: **Plain Old Data Object** — sin clases, sin estado. Solo exports.

```js
// ISR: progressive brackets
export const ISR_RATES = {
  brackets: [
    { min: 0, max: 4064.00, rate: 0, label: 'Exento' },
    { min: 4064.01, max: 9142.86, rate: 0.10, label: '10%' },
    { min: 9142.87, max: 22857.14, rate: 0.20, label: '20%' },
    { min: 22857.15, max: Infinity, rate: 0.30, label: '30%' },
  ],
  dependentDeduction: 800,
};

// IVA
export const IVA_RATE = 0.13;

// ISC
export const ISC_RATES = { ... };

// Patrimonio
export const PATRIMONIO_RATE = 0.01;
```

### `src/data/constants.js`

```js
export const APP = { name, fullName, tagline, founded };
export const CONTACT = { email, phone, address, hours, saturdayHours };
export const LINKS = { terms, privacy, about, blog };
export const SOCIAL = { github, twitter, facebook };
```

## Component Changes

### ISRCalculator.jsx
1. Import `ISR_RATES` from `../data/taxRates`
2. Replace hardcoded brackets → `ISR_RATES.brackets` loop
3. Replace dependentDeduction → `ISR_RATES.dependentDeduction`
4. Guard: `taxableIncome` → `Number.isNaN` check → show `"0.00"`
5. Validation: `!income` → `income === ''`

### IVACalculator.jsx
1. Import `IVA_RATE` from `../data/taxRates`
2. Replace `0.13` → `IVA_RATE`
3. Validation: `!saleAmount` → `saleAmount === ''`

### ISCCalculator.jsx
1. Import `ISC_RATES` from `../data/taxRates`
2. Replace static object → `ISC_RATES`
3. Validation: `!amount` → `amount === ''`

### PatrimonioCalculator.jsx
1. Import `PATRIMONIO_RATE` from `../data/taxRates`
2. Replace `0.01` → `PATRIMONIO_RATE`
3. Validation: ALL fields check `=== ''` instead of `!value`

### Header.jsx
- Line 51: `text-green-700` → `text-blue-700`

### Footer.jsx
- Import `APP`, `CONTACT`, `LINKS`, `SOCIAL`
- Replace hardcoded text with `APP.name`, `CONTACT.email`, etc.

### ContactPage.jsx
- Import `CONTACT`
- Replace hardcoded contact info

### index.css
- Change `a` global selector:
  - Remove `text-green-600`, `hover:text-red-700`
  - Keep `underline` only (or remove the global rule entirely)
  - Apply link styles per-component where needed

## Validation Pattern

**Before (broken):**
```jsx
disabled={!income || !expenses}
```

**After (correct):**
```jsx
disabled={income === '' || expenses === ''}
```

For optional fields (dependents in ISR):
```jsx
disabled={income === '' || expenses === '' || socialContribution === ''}
// dependents defaults to 0 — not in the check
```

## Open Questions / Decisiones

1. **NaN guard**: ¿guard clause temprano en `calculateTax()` o `Number(value) || 0` en display?
   → Decisión: guard clause en calculateTax + `Number(value) || 0` en display.

2. **CSS global a**: ¿eliminar o corregir?
   → Decisión: eliminar el global `a` — los componentes ya estilan sus links.

3. **Constants**: ¿email/phone reales o mantener placeholders `2XXX XXXX`?
   → Decisión: mantener placeholders — no tenemos datos reales del cliente.
