"""Reproducible RFM customer segmentation.

Methodology
-----------
1. Build Recency / Frequency / Monetary per customer from ``fact_sales``:
   * recency  = days between the customer's last order and the analysis date
                (the latest order date in the data).
   * frequency = number of distinct orders.
   * monetary  = net revenue kept (revenue - refund_amount).
2. Score each dimension 1..5 using **rank-based quintiles** (equal-sized groups),
   which avoids duplicate-edge errors from ties and guarantees non-null scores.
   * R: fewer days -> higher score (5 = most recent).
   * F / M: higher value -> higher score (5 = best).
3. Map (R, F, M) to five mutually exclusive, fully covering business segments via
   an ordered decision ladder (first match wins). Customers without any purchase
   are appended as "Clientes inactivos" with the lowest scores.

Outputs ``data/processed/customer_rfm.csv`` (one row per customer, Power BI ready),
figures in ``reports/figures/`` and ``reports/customer_segmentation.md``.

Run with:  ``python -m src.customer_segmentation``
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import seaborn as sns

from src import config

FIGDIR = config.REPORTS_DIR / "figures"
OUTPUT_CSV = config.PROCESSED_DATA_DIR / "customer_rfm.csv"
SOURCE_NOTE = "Datos simulados (semilla 42) — proyecto de portafolio"

# Exact segment labels (Spanish, as required).
SEG_VIP = "VIP"
SEG_FREQUENT = "Clientes frecuentes"
SEG_NEW = "Nuevos clientes"
SEG_AT_RISK = "Clientes en riesgo"
SEG_INACTIVE = "Clientes inactivos"

SEGMENT_ORDER = [SEG_VIP, SEG_FREQUENT, SEG_NEW, SEG_AT_RISK, SEG_INACTIVE]
SEGMENT_COLORS = {
    SEG_VIP: "#55A868",
    SEG_FREQUENT: "#4C72B0",
    SEG_NEW: "#8172B3",
    SEG_AT_RISK: "#DD8452",
    SEG_INACTIVE: "#C44E52",
}


# --------------------------------------------------------------------------
# RFM computation
# --------------------------------------------------------------------------
def compute_rfm(t: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.Timestamp]:
    """Per-customer R/F/M for customers with at least one order."""
    s = t["fact_sales"].copy()
    s["revenue"] = s["quantity"] * s["unit_price"] - s["discount_amount"] + s["shipping_revenue"]
    s["order_dt"] = pd.to_datetime(s["order_date"])
    analysis_date = s["order_dt"].max()

    rfm = s.groupby("customer_id").agg(
        last_order_date=("order_dt", "max"),
        frequency=("order_id", "nunique"),
        monetary=("revenue", lambda x: x.sum()),
        refund=("refund_amount", "sum"),
    ).reset_index()
    rfm["monetary"] = (rfm["monetary"] - rfm["refund"]).round(2)
    rfm = rfm.drop(columns="refund")
    rfm["recency_days"] = (analysis_date - rfm["last_order_date"]).dt.days
    return rfm.sort_values("customer_id").reset_index(drop=True), analysis_date


def score_rfm(rfm: pd.DataFrame) -> pd.DataFrame:
    """Assign 1..5 scores via rank-based quintiles (no nulls, no tie errors)."""
    r = rfm.copy()
    # Recency: smallest days = best = 5.
    r["r_score"] = pd.qcut(r["recency_days"].rank(method="first"),
                           5, labels=[5, 4, 3, 2, 1]).astype(int)
    # Frequency / Monetary: largest = best = 5.
    r["f_score"] = pd.qcut(r["frequency"].rank(method="first"),
                           5, labels=[1, 2, 3, 4, 5]).astype(int)
    r["m_score"] = pd.qcut(r["monetary"].rank(method="first"),
                           5, labels=[1, 2, 3, 4, 5]).astype(int)
    r["rfm_score"] = r["r_score"] * 100 + r["f_score"] * 10 + r["m_score"]
    r["rfm_cell"] = (r["r_score"].astype(str) + r["f_score"].astype(str)
                     + r["m_score"].astype(str))
    return r


def assign_segment(r_score: int, f_score: int, m_score: int) -> str:
    """Ordered decision ladder — mutually exclusive, fully covering."""
    if m_score >= 4 and f_score >= 4 and r_score >= 3:
        return SEG_VIP
    if r_score <= 2 and (f_score >= 3 or m_score >= 4):
        return SEG_AT_RISK
    if r_score <= 2:
        return SEG_INACTIVE
    if f_score <= 2 and r_score >= 3:
        return SEG_NEW
    return SEG_FREQUENT


def build_all_customers(t: dict[str, pd.DataFrame], scored: pd.DataFrame,
                        analysis_date: pd.Timestamp) -> pd.DataFrame:
    """Attach customer attributes and append non-purchasers as inactive."""
    scored = scored.copy()
    scored["segment"] = [assign_segment(r, f, m) for r, f, m
                         in zip(scored["r_score"], scored["f_score"], scored["m_score"])]
    scored["has_purchase"] = 1

    cust = t["dim_customer"]
    non_buyers = cust[~cust["customer_id"].isin(scored["customer_id"])].copy()
    if len(non_buyers):
        acq = pd.to_datetime(non_buyers["acquisition_date"])
        nb = pd.DataFrame({
            "customer_id": non_buyers["customer_id"].to_numpy(),
            "last_order_date": pd.NaT,
            "frequency": 0,
            "monetary": 0.0,
            "recency_days": (analysis_date - acq).dt.days.to_numpy(),
            "r_score": 1, "f_score": 1, "m_score": 1,
            "rfm_score": 111, "rfm_cell": "111",
            "segment": SEG_INACTIVE, "has_purchase": 0,
        })
        scored = pd.concat([scored, nb], ignore_index=True)

    out = scored.merge(
        cust[["customer_id", "customer_segment", "city", "region",
              "acquisition_date", "acquisition_channel"]],
        on="customer_id", how="left",
    )
    out["last_order_date"] = out["last_order_date"].astype("string")
    return out.sort_values("customer_id").reset_index(drop=True)


# --------------------------------------------------------------------------
# Visualizations
# --------------------------------------------------------------------------
def _save(fig, name: str) -> None:
    fig.text(0.01, 0.01, SOURCE_NOTE, fontsize=7, color="gray", alpha=0.8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIGDIR / name, dpi=120, bbox_inches="tight")
    plt.close(fig)


def figures(df: pd.DataFrame) -> None:
    FIGDIR.mkdir(parents=True, exist_ok=True)
    present = [s for s in SEGMENT_ORDER if s in set(df["segment"])]
    palette = [SEGMENT_COLORS[s] for s in present]

    # Count + total monetary per segment.
    summary = df.groupby("segment").agg(
        customers=("customer_id", "size"),
        total_monetary=("monetary", "sum"),
    ).reindex(present).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    sns.barplot(data=summary, x="customers", y="segment", hue="segment",
                palette=SEGMENT_COLORS, legend=False, ax=axes[0], order=present)
    axes[0].set_title("Clientes por segmento", weight="bold")
    axes[0].set_xlabel("Clientes"); axes[0].set_ylabel("")
    for i, v in enumerate(summary["customers"]):
        axes[0].text(v, i, f" {v:,.0f}", va="center", fontsize=9)

    sns.barplot(data=summary, x="total_monetary", y="segment", hue="segment",
                palette=SEGMENT_COLORS, legend=False, ax=axes[1], order=present)
    axes[1].set_title("Valor (monetary) por segmento", weight="bold")
    axes[1].set_xlabel("Total monetary"); axes[1].set_ylabel("")
    axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    _save(fig, "09_segments_size_value.png")

    # R vs F scatter coloured by segment (buyers only).
    buyers = df[df["has_purchase"] == 1]
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.scatterplot(data=buyers, x="recency_days", y="frequency", hue="segment",
                    palette=SEGMENT_COLORS, hue_order=present, alpha=0.6,
                    size="monetary", sizes=(20, 300), ax=ax)
    ax.set_title("Segmentos RFM: Recency vs Frequency", fontsize=13, weight="bold")
    ax.set_xlabel("Recency (días desde última compra)"); ax.set_ylabel("Frequency (pedidos)")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    _save(fig, "10_segments_recency_frequency.png")


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------
RECOMMENDATIONS = {
    SEG_VIP: "Programa de fidelización premium, acceso anticipado y atención "
             "preferente. Proteger la relación: son la principal fuente de valor.",
    SEG_FREQUENT: "Incentivar mayor ticket y cross-sell; upgrade hacia VIP con "
                  "beneficios por volumen. Mantener la cadencia de compra.",
    SEG_NEW: "Onboarding y segunda compra: emails de bienvenida, descuento de "
             "reactivación acotado y recomendación de productos afines.",
    SEG_AT_RISK: "Campaña de recuperación priorizada por monetary: recordatorio, "
                 "oferta personalizada y encuesta de motivos de abandono.",
    SEG_INACTIVE: "Reactivación de bajo costo (email masivo) o depuración de la "
                  "base. Evitar inversión alta: baja probabilidad de retorno.",
}


def build_report(df: pd.DataFrame, scored: pd.DataFrame,
                 analysis_date: pd.Timestamp, n_total_customers: int) -> str:
    total = len(df)
    dist = df.groupby("segment").agg(
        customers=("customer_id", "size"),
        avg_recency=("recency_days", "mean"),
        avg_frequency=("frequency", "mean"),
        total_monetary=("monetary", "sum"),
        avg_monetary=("monetary", "mean"),
    ).reindex([s for s in SEGMENT_ORDER if s in set(df["segment"])]).reset_index()
    dist["pct_customers"] = 100 * dist["customers"] / total
    dist["pct_value"] = 100 * dist["total_monetary"] / dist["total_monetary"].sum()

    dist_rows = "\n".join(
        f"| {r.segment} | {r.customers:,.0f} | {r.pct_customers:.1f}% | "
        f"{r.avg_recency:.0f} | {r.avg_frequency:.1f} | {r.total_monetary:,.0f} | "
        f"{r.pct_value:.1f}% |"
        for r in dist.itertuples()
    )

    # Documented thresholds: metric range per score band (buyers only).
    def _bounds(col: str) -> str:
        b = scored.groupby(f"{col[0]}_score")[col].agg(["min", "max"]).sort_index()
        return "\n".join(f"| {score} | {row['min']:,.2f} | {row['max']:,.2f} |"
                         for score, row in b.iterrows())

    reco_rows = "\n".join(
        f"### {seg}\n{RECOMMENDATIONS[seg]}\n" for seg in SEGMENT_ORDER if seg in set(df["segment"])
    )

    return f"""# Segmentación de Clientes (RFM)

> **Datos simulados** (semilla 42). Metodología reproducible; todas las cifras se
> calculan desde `data/processed/`. Resultado: `data/processed/customer_rfm.csv`.

## 1. Metodología

- **Fecha de análisis:** {analysis_date.date()} (último pedido en los datos).
- **Recency** = días desde la última compra. **Frequency** = pedidos distintos.
  **Monetary** = revenue neto de devoluciones.
- **Puntuación 1–5 por quintiles basados en rango** (grupos de igual tamaño): evita
  errores por empates y garantiza puntuaciones no nulas. R: menos días → 5.
  F y M: mayor valor → 5.
- **Base RFM:** {len(scored):,} clientes con al menos un pedido, de {n_total_customers:,}
  totales. Los {n_total_customers - len(scored):,} clientes sin compras se incluyen como
  "{SEG_INACTIVE}" (scores mínimos), de modo que **cada cliente tiene un segmento**.

## 2. Umbrales por puntuación (clientes con compra)

Rangos del valor subyacente en cada banda de score:

**Recency (días)** — score 5 = compra más reciente
| r_score | min | max |
|---|---:|---:|
{_bounds("recency_days")}

**Frequency (pedidos)** — score 5 = mayor frecuencia
| f_score | min | max |
|---|---:|---:|
{_bounds("frequency")}

**Monetary** — score 5 = mayor valor
| m_score | min | max |
|---|---:|---:|
{_bounds("monetary")}

## 3. Definición de segmentos (escalera de decisión, primer match gana)

1. **{SEG_VIP}:** `M≥4 y F≥4 y R≥3` (alto valor y aún activos).
2. **{SEG_AT_RISK}:** `R≤2 y (F≥3 o M≥4)` (fueron valiosos, dejaron de comprar).
3. **{SEG_INACTIVE}:** `R≤2` restantes (baja recencia y bajo valor) + clientes sin compras.
4. **{SEG_NEW}:** `F≤2 y R≥3` (pocas compras, recientes).
5. **{SEG_FREQUENT}:** resto (`R≥3 y F≥3`, compradores recurrentes no-VIP).

La escalera es **mutuamente excluyente y cubre el 100%** de las combinaciones R×F×M.

## 4. Distribución de segmentos

| Segmento | Clientes | % clientes | Recency prom. | Freq. prom. | Monetary total | % valor |
|---|---:|---:|---:|---:|---:|---:|
{dist_rows}

## 5. Recomendaciones por segmento

{reco_rows}
## 6. Uso en Power BI

`customer_rfm.csv` tiene **una fila por cliente** con columnas planas listas para
modelar: `customer_id` (clave), `segment`, `r_score`/`f_score`/`m_score`,
`rfm_score`, `recency_days`, `frequency`, `monetary`, `has_purchase` y atributos
de cliente. Se relaciona con `dim_customer[customer_id]` (1:1) para filtrar todo
el modelo por segmento.

## 7. Limitaciones del método

- **RFM es descriptivo/histórico:** no predice comportamiento futuro ni CLV probabilístico.
- **Quintiles por rango:** los empates (p. ej. muchos clientes con 1 pedido) se
  reparten por orden estable; los cortes son relativos a esta base, no absolutos.
- **Umbrales de segmento** (≥3, ≥4, ≤2) son una convención de negocio, no óptimos
  estadísticos; ajustables según estrategia.
- **Clientes sin compras** se marcan inactivos con recency basada en la fecha de
  adquisición (proxy), no en una compra real.
- Datos **simulados**: la distribución refleja el generador, no un negocio real.
"""


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def run() -> pd.DataFrame:
    sns.set_theme(style="whitegrid", palette="deep")
    config.ensure_directories()
    FIGDIR.mkdir(parents=True, exist_ok=True)

    t = {name: pd.read_csv(config.PROCESSED_DATA_DIR / config.RAW_FILES[name])
         for name in config.RAW_FILES}
    n_total = len(t["dim_customer"])

    rfm, analysis_date = compute_rfm(t)
    scored = score_rfm(rfm)
    df = build_all_customers(t, scored, analysis_date)

    cols = ["customer_id", "segment", "has_purchase",
            "recency_days", "frequency", "monetary",
            "r_score", "f_score", "m_score", "rfm_score", "rfm_cell",
            "last_order_date", "customer_segment", "city", "region",
            "acquisition_date", "acquisition_channel"]
    df[cols].to_csv(OUTPUT_CSV, index=False)

    figures(df)
    report = build_report(df, scored, analysis_date, n_total)
    (config.REPORTS_DIR / "customer_segmentation.md").write_text(report, encoding="utf-8")
    return df[cols]


def main() -> None:
    df = run()
    print(f"RFM segmentation written to {OUTPUT_CSV}  ({len(df):,} customers)")
    print("Segment distribution:")
    dist = df["segment"].value_counts()
    for seg in SEGMENT_ORDER:
        if seg in dist:
            print(f"  {seg:22s} {dist[seg]:>6,}  ({100*dist[seg]/len(df):4.1f}%)")
    print("Nulls in scores:",
          int(df[["r_score", "f_score", "m_score"]].isna().sum().sum()))


if __name__ == "__main__":
    main()
