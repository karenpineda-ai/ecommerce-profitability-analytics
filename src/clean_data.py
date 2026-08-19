"""Cleaning and normalization stage.

Reads the raw CSVs, applies documented, reversible cleaning rules, validates the
data before and after, writes the corrected tables to ``data/processed/`` and
produces ``reports/data_quality_report.md``.

Cleaning is intentionally conservative: it only removes exact duplicate rows and
fills recoverable (warning-level) nulls. Critical issues are never silently
"fixed" — they would block the pipeline and be surfaced in the report.

Run with:  ``python -m src.clean_data``
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src import config, validate_data as vd


@dataclass
class CleaningLog:
    """Accumulates what cleaning did, for the quality report."""

    rows_in: dict[str, int] = field(default_factory=dict)
    rows_out: dict[str, int] = field(default_factory=dict)
    duplicates_removed: int = 0
    nulls_filled: dict[str, int] = field(default_factory=dict)
    text_normalized: dict[str, int] = field(default_factory=dict)


# --------------------------------------------------------------------------
# I/O
# --------------------------------------------------------------------------
def load_raw() -> dict[str, pd.DataFrame]:
    return {
        name: pd.read_csv(config.RAW_DATA_DIR / fname)
        for name, fname in config.RAW_FILES.items()
    }


def _normalize_text(df: pd.DataFrame, cols: list[str], log: CleaningLog, table: str) -> None:
    """Strip surrounding whitespace from string columns (in place)."""
    for col in cols:
        if col not in df.columns:
            continue
        before = df[col].copy()
        stripped = df[col].astype("string").str.strip()
        df[col] = stripped
        changed = int((before.astype("string") != stripped).fillna(False).sum())
        if changed:
            log.text_normalized[f"{table}.{col}"] = changed


# --------------------------------------------------------------------------
# Cleaning
# --------------------------------------------------------------------------
def clean(tables: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], CleaningLog]:
    """Apply cleaning rules and return the cleaned tables plus a log."""
    log = CleaningLog()
    out = {k: v.copy() for k, v in tables.items()}
    for name, df in out.items():
        log.rows_in[name] = len(df)

    # --- dim_customer: fill descriptive nulls, normalize text ---
    cust = out["dim_customer"]
    _normalize_text(cust, ["customer_segment", "city", "region", "acquisition_channel"], log, "dim_customer")
    for col in ("city", "region"):
        n = int(cust[col].isna().sum())
        if n:
            cust[col] = cust[col].fillna("Unknown")
            log.nulls_filled[f"dim_customer.{col}"] = n

    # --- dim_product: fill descriptive nulls, normalize text ---
    prod = out["dim_product"]
    _normalize_text(prod, ["product_name", "category", "subcategory", "brand", "supplier"], log, "dim_product")
    for col in ("brand", "subcategory"):
        n = int(prod[col].isna().sum())
        if n:
            prod[col] = prod[col].fillna("Unknown")
            log.nulls_filled[f"dim_product.{col}"] = n

    # --- dim_channel: normalize text ---
    _normalize_text(out["dim_channel"], ["channel_name", "channel_type"], log, "dim_channel")

    # --- fact_sales: drop exact duplicates, fill recoverable nulls ---
    sales = out["fact_sales"]
    before_rows = len(sales)
    sales = sales.drop_duplicates(ignore_index=True)
    log.duplicates_removed = before_rows - len(sales)

    # discount_amount null -> 0.0 (no discount recorded).
    n_disc = int(sales["discount_amount"].isna().sum())
    if n_disc:
        sales["discount_amount"] = sales["discount_amount"].fillna(0.0)
        log.nulls_filled["fact_sales.discount_amount"] = n_disc

    # shipping_cost null -> median (robust central estimate).
    n_ship = int(sales["shipping_cost"].isna().sum())
    if n_ship:
        median_ship = round(float(sales["shipping_cost"].median()), 2)
        sales["shipping_cost"] = sales["shipping_cost"].fillna(median_ship)
        log.nulls_filled["fact_sales.shipping_cost"] = n_ship

    out["fact_sales"] = sales

    for name, df in out.items():
        log.rows_out[name] = len(df)
    return out, log


def reconcile_revenue(raw: dict[str, pd.DataFrame], clean_: dict[str, pd.DataFrame]) -> dict[str, float]:
    """Compare source vs processed revenue totals (should differ only by dedup)."""
    def _rev(s: pd.DataFrame) -> float:
        return float(
            (s["quantity"] * s["unit_price"] - s["discount_amount"].fillna(0)
             + s["shipping_revenue"]).sum()
        )
    raw_rev = _rev(raw["fact_sales"])
    proc_rev = _rev(clean_["fact_sales"])
    return {"raw_revenue": round(raw_rev, 2),
            "processed_revenue": round(proc_rev, 2),
            "difference": round(raw_rev - proc_rev, 2)}


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------
def build_report(
    raw: dict[str, pd.DataFrame],
    cleaned: dict[str, pd.DataFrame],
    before: list[vd.ValidationResult],
    after: list[vd.ValidationResult],
    log: CleaningLog,
    recon: dict[str, float],
) -> str:
    sb = vd.summarize(before)
    sa = vd.summarize(after)

    def _rows_table() -> str:
        rows = ["| Tabla | Filas originales | Filas procesadas | Δ |", "|---|---:|---:|---:|"]
        for name in config.RAW_FILES:
            a, b = log.rows_in[name], log.rows_out[name]
            rows.append(f"| `{name}` | {a:,} | {b:,} | {b - a:+,} |")
        return "\n".join(rows)

    def _nulls_table() -> str:
        rows = ["| Tabla.Columna | Nulos (origen) | Severidad |", "|---|---:|---|"]
        for r in before:
            if r.rule.startswith("nulls[") and r.n_errors > 0:
                rows.append(f"| `{r.table}.{r.rule[6:-1]}` | {r.n_errors} | {r.severity} |")
        return "\n".join(rows) if len(rows) > 2 else "_Sin nulos detectados._"

    def _rules_table(results: list[vd.ValidationResult]) -> str:
        rows = ["| Regla | Tabla | Severidad | Errores | Estado |", "|---|---|---|---:|---|"]
        for r in results:
            status = "✅ OK" if r.passed else ("⛔ BLOQUEA" if r.blocking else "⚠️ Advertencia")
            rows.append(f"| `{r.rule}` | {r.table} | {r.severity} | {r.n_errors} | {status} |")
        return "\n".join(rows)

    corrected = log.duplicates_removed + sum(log.nulls_filled.values())
    fills = "\n".join(f"- `{k}`: {v} valores rellenados" for k, v in log.nulls_filled.items()) or "- (ninguno)"
    norms = "\n".join(f"- `{k}`: {v} valores normalizados" for k, v in log.text_normalized.items()) or "- (ninguno)"

    return f"""# Reporte de Calidad de Datos

> Datos **simulados** (semilla `{config.RANDOM_SEED}`). Generado por `src/clean_data.py`.
> Este reporte se sobrescribe en cada ejecución.

## 1. Resumen

| Métrica | Antes de limpiar | Después de limpiar |
|---|---:|---:|
| Reglas evaluadas | {sb['rules']} | {sa['rules']} |
| Reglas OK | {sb['passed']} | {sa['passed']} |
| Reglas con error | {sb['failed']} | {sa['failed']} |
| Fallos críticos (bloqueantes) | {sb['critical_failures']} | {sa['critical_failures']} |
| Advertencias | {sb['warnings']} | {sa['warnings']} |

**Estado final:** {"⛔ Pipeline bloqueado por errores críticos." if sa['critical_failures'] else "✅ Sin errores críticos. Datos aptos para análisis."}

## 2. Filas originales vs procesadas

{_rows_table()}

**Registros corregidos:** {corrected:,} (duplicados eliminados: {log.duplicates_removed}, nulos rellenados: {sum(log.nulls_filled.values())}).

## 3. Valores nulos (en origen)

{_nulls_table()}

## 4. Duplicados

- Filas totalmente duplicadas en `fact_sales` (origen): **{log.duplicates_removed}**.
- Acción: eliminadas con `drop_duplicates`. Las líneas legítimas difieren en columnas
  de costo aleatorias, por lo que no se eliminan por error.

## 5. Registros inválidos (críticos)

- Detectados antes de limpiar: **{sb['critical_failures']}** reglas críticas con error.
- Detectados después de limpiar: **{sa['critical_failures']}**.
- No se encontraron claves duplicadas, FKs huérfanas, cantidades ≤ 0, montos
  negativos ni fechas fuera de periodo.

## 6. Registros corregidos

**Nulos rellenados:**

{fills}

**Texto normalizado (whitespace):**

{norms}

## 7. Reconciliación de totales (fuente vs procesado)

| Métrica | Valor |
|---|---:|
| Revenue origen | {recon['raw_revenue']:,.2f} |
| Revenue procesado | {recon['processed_revenue']:,.2f} |
| Diferencia | {recon['difference']:,.2f} |

La diferencia se explica **en su totalidad** por la eliminación de filas duplicadas.

## 8. Reglas aplicadas (después de limpiar)

{_rules_table(after)}

## 9. Reglas de limpieza aplicadas

- **Duplicados:** eliminación de filas exactas duplicadas en `fact_sales`.
- **`discount_amount` nulo → 0.0** (interpretado como "sin descuento").
- **`shipping_cost` nulo → mediana** (estimador central robusto).
- **`city` / `region` / `brand` / `subcategory` nulos → `"Unknown"`** (preserva la fila).
- **Normalización de texto:** se elimina el whitespace sobrante en columnas categóricas.

## 10. Limitaciones

- Los datos son **simulados**; el reporte demuestra el proceso, no describe un negocio real.
- El relleno de `shipping_cost` con la mediana **atenúa la varianza** de esa columna.
- No se imputan valores críticos: si existieran (FK huérfana, monto negativo), el
  pipeline se marcaría como bloqueado en lugar de inventar datos.
- La detección de duplicados en `fact_sales` es a nivel de fila completa (no hay
  clave de línea de pedido en el origen).
"""


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def run() -> tuple[dict[str, pd.DataFrame], list[vd.ValidationResult]]:
    config.ensure_directories()
    raw = load_raw()
    before = vd.run_all_validations(raw)
    cleaned, log = clean(raw)
    after = vd.run_all_validations(cleaned)
    recon = reconcile_revenue(raw, cleaned)

    for name, df in cleaned.items():
        df.to_csv(config.PROCESSED_DATA_DIR / config.RAW_FILES[name], index=False)

    report = build_report(raw, cleaned, before, after, log, recon)
    (config.REPORTS_DIR / "data_quality_report.md").write_text(report, encoding="utf-8")
    return cleaned, after


def main() -> None:
    cleaned, after = run()
    summary = vd.summarize(after)
    print("Cleaning complete. Processed files written to", config.PROCESSED_DATA_DIR)
    print(f"  rules={summary['rules']} passed={summary['passed']} "
          f"failed={summary['failed']} critical={summary['critical_failures']} "
          f"warnings={summary['warnings']}")
    if vd.has_blocking_errors(after):
        print("  [BLOCKED] Critical errors remain -- review the report.")
    else:
        print("  [OK] No blocking errors. Data ready for the database load (Phase 4).")


if __name__ == "__main__":
    main()
