# Tasks: improve-tax-assistant — PR #1 (Bug Fixes + De-hardcoding)

## Review Workload Forecast
- Estimated changed lines: ~150
- Chained PRs recommended: Yes (PR #1 of 3)
- 400-line budget risk: Low
- Decision needed before apply: No (already approved)

## Tasks

### T1: Create data layer — `src/data/`
**Files**: `src/data/taxRates.js`, `src/data/constants.js`
**Dependencies**: None
**Risk**: Low
**Status**: ✅ Done

Created two config modules:
- `taxRates.js`: ISR brackets, IVA rate, ISC categories, Patrimonio rate
- `constants.js`: APP name/tagline, CONTACT info, LINKS, SOCIAL

### T2: Fix validation bug — accept "0" as valid input
**Files**: `ISRCalculator.jsx`, `IVACalculator.jsx`, `ISCCalculator.jsx`, `PatrimonioCalculator.jsx`
**Dependencies**: None (can run parallel to T1)
**Risk**: Low
**Status**: ✅ Done

Changed all `!value` checks to `value === ''` in:
- `disabled` props on buttons
- Any conditional rendering based on field values
- Keep optional fields out of the check (dependents defaults to 0)

### T3: Fix NaN display in ISRCalculator
**Files**: `ISRCalculator.jsx`
**Dependencies**: T1 (needs ISR_RATES)
**Risk**: Low
**Status**: ✅ Done

- Added guard clause using `hasRequiredFields`: display `"0.00"` when empty
- Changed `parseFloat(value)` → `Number(value)` for consistency

### T4: Refactor ISRCalculator to use taxRates config
**Files**: `ISRCalculator.jsx`
**Dependencies**: T1 ✅, T2 ✅, T3 ✅
**Risk**: Medium (logic change)
**Status**: ✅ Done

- Import `ISR_RATES` from `../data/taxRates`
- Replaced bracket constants with `ISR_RATES.brackets` array iteration
- Used `ISR_RATES.dependentDeduction`
- Tax calculated by iterating brackets (progressive loop)

### T5: Refactor IVACalculator to use taxRates config
**Files**: `IVACalculator.jsx`
**Dependencies**: T1 ✅, T2 ✅
**Risk**: Low
**Status**: ✅ Done

- Import `IVA_RATE`
- Replace `0.13` with `IVA_RATE`

### T6: Refactor ISCCalculator to use taxRates config
**Files**: `ISCCalculator.jsx`
**Dependencies**: T1 ✅, T2 ✅
**Risk**: Low
**Status**: ✅ Done

- Import `ISC_RATES`
- Replaced hardcoded object with imported data

### T7: Refactor PatrimonioCalculator to use taxRates config
**Files**: `PatrimonioCalculator.jsx`
**Dependencies**: T1 ✅, T2 ✅
**Risk**: Low
**Status**: ✅ Done

- Import `PATRIMONIO_RATE`
- Replace `0.01` with `PATRIMONIO_RATE`

### T8: Fix CSS global link colors
**Files**: `index.css`
**Dependencies**: None
**Risk**: Low
**Status**: ✅ Done

- Removed `@apply text-green-600 hover:text-red-700 underline` from global `a`
- Kept `underline` only

### T9: Fix Header nav active color
**Files**: `Header.jsx`
**Dependencies**: T8 (verify no conflict)
**Risk**: Low
**Status**: ✅ Done

- Changed `text-green-700` → `text-blue-700` in active nav item

### T10: Refactor Footer to use constants
**Files**: `Footer.jsx`
**Dependencies**: T1 ✅
**Risk**: Low
**Status**: ✅ Done

- Import `APP`, `CONTACT`, `LINKS`, `SOCIAL`
- Replaced hardcoded strings with config values

### T11: Refactor ContactPage to use constants + add form handlers
**Files**: `ContactPage.jsx`
**Dependencies**: T1 ✅
**Risk**: Medium
**Status**: ✅ Done

- Import `CONTACT` from `../data/constants`
- Added: form state, validation (name, email regex, subject, message), submit handler with loading/success/error states
- Added: ARIA attributes (aria-invalid, aria-describedby, role="alert")
- Added: success screen with reset button
- Replaced hardcoded contact info with CONTACT constants

## Dependency Graph

```
T1 (data layer)
├── T4 (ISR calc) ← T2, T3
├── T5 (IVA calc) ← T2
├── T6 (ISC calc) ← T2
├── T7 (Patr calc) ← T2
├── T10 (Footer) 
└── T11 (ContactPage)

T2 (validation bug) → T4, T5, T6, T7
T3 (NaN fix) → T4
T8 (CSS links) → T9
T9 (Header color) ← T8

Independent: T8
```

## Execution Order

```
Round 1: T1 + T2 + T3 + T8 (parallel — no deps between them)
Round 2: T4 + T5 + T6 + T7 + T9 + T10 + T11 (wait for deps)
```

## Verification

After all tasks:
1. `npm run dev` → compila sin errores
2. Calculadora ISR: income=0, expenses=0, dependents=0, social=0 → tax=0
3. Calculadora IVA: amount=100, no exento → IVA=13
4. Calculadora ISC: amount=100, tabaco → ISC=100
5. Calculadora Patrimonio: todos los campos en 0 → tax=0
6. Links en Footer y ContactPage son azules (no verdes)
7. Nav activo en Header es azul
8. `npm run build` → build exitoso
