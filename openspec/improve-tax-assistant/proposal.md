# Change Proposal: improve-tax-assistant

## Intent
Corregir bugs, des-hardcodear configuraciones tributarias, implementar funcionalidad faltante y agregar infraestructura base (TypeScript, tests, git) en el Asistente Tributario SV.

## Scope
**Origen**: Frontend completo (calculadoras, páginas, layout, CSS).
**19 hallazgos** categorizados en 3 PRs encadenados.

---

## PR #1: Bug Fixes + De-hardcoding + CSS Fixes
**Target**: `feature/improve-tax-assistant` (tracker branch)

### Deliberables
| # | Hallazgo | Archivos | Tipo |
|---|----------|----------|------|
| 1 | `!campo` rechaza `"0"` como input válido | ISRCalculator, IVACalculator, ISCCalculator, PatrimonioCalculator | Bug |
| 2 | `parseFloat('')` → NaN en ISRCalculator | ISRCalculator | Bug |
| 3 | Selector global `a { color: green }` rompe links | index.css | Bug |
| 4 | Nav item activo con `text-green-700` inconsistente | Header.jsx | Bug |
| 5 | Tramos/tasas ISR harcodeados | ISRCalculator + **nuevo** `src/data/taxRates.js` | De-hardcode |
| 6 | Tasa IVA harcodeada | IVACalculator + taxRates.js | De-hardcode |
| 7 | Tasas ISC harcodeadas | ISCCalculator + taxRates.js | De-hardcode |
| 8 | Tasa Patrimonio harcodeada | PatrimonioCalculator + taxRates.js | De-hardcode |
| 9 | Textos corporativos harcodeados | Footer, ContactPage, DocumentosPage + **nuevo** `src/data/constants.js` | De-hardcode |

---

## PR #2: Feature Completion
**Target**: Branch de PR #1 (revision diff acotada)

### Deliberables
| # | Hallazgo | Archivos | Tipo |
|---|----------|----------|------|
| 10 | onChange vacío → persistir resultados activos en CalculatorPage | CalculatorPage | Feature |
| 11 | DocumentosPage placeholder → contenido real con recursos | DocumentosPage, + nuevos components | Feature |
| 12 | LoginPage sin handlers ni auth | LoginPage | Feature |
| 13 | ContactPage sin onSubmit ni validación | ContactPage | Feature |
| 14 | HomePage servicios no clickeables | HomePage | Feature |
| 15 | Sin estados loading/error/empty | Todas las páginas | Feature |

---

## PR #3: Infrastructure + Polish
**Target**: Branch de PR #2 (revision diff acotada)

### Deliberables
| # | Hallazgo | Archivos | Tipo |
|---|----------|----------|------|
| 18 | Sin git repo | root (git init) | Infra |
| 16 | Sin TypeScript | Global + `tsconfig.json`, `vite.config` update | Infra |
| 17 | Sin tests | `vitest.config`, tests unitarios calculadoras | Infra |
| 19 | Sin accesibilidad | Todos los componentes | Polish |

---

## Riesgos
- **Scope creep**: TypeScript en todo el proyecto es un cambio masivo — limitar a componentes activos primero
- **Regresión**: Sin tests actuales, hay que verificar manualmente cada calculadora
- **Chain complexity**: PR #2 depende de PR #1, PR #3 depende de PR #2 — coordinar merges

## Success Criteria
- [ ] Todas las calculadoras aceptan `0` como input válido
- [ ] Todas las tasas/tramos viven en `src/data/taxRates.js`
- [ ] `DocumentosPage` muestra contenido real
- [ ] Formularios Contact/Login tienen handlers y validación
- [ ] Proyecto compila y corre sin errores (`npm run dev`)
- [ ] tests pasan (`npm run test`)
- [ ] TypeScript strict mode activado en rutas principales
