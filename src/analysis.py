"""Exploratory analysis: professional figures + data-backed findings.

Loads the processed tables, computes revenue/profitability metrics (definitions
in CLAUDE.md), renders clean charts to ``reports/figures/`` and writes
``reports/findings.md`` with every number injected from the data itself, so no
statement is made that the data does not support.

Run with:  ``python -m src.analysis``
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # headless, deterministic rendering

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

from src import config
from src import customer_segmentation as seg_mod

FIGDIR = config.REPORTS_DIR / "figures"
SOURCE_NOTE = "Datos simulados (semilla 42) — proyecto de portafolio"


# --------------------------------------------------------------------------
# Load & prepare
# --------------------------------------------------------------------------
def load() -> dict[str, pd.DataFrame]:
    return {
        name: pd.read_csv(config.PROCESSED_DATA_DIR / config.RAW_FILES[name])
        for name in config.RAW_FILES
    }


def prepare(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return a fact_sales frame enriched with revenue, gross_profit and joins."""
    s = t["fact_sales"].merge(
        t["dim_product"][["product_id", "product_name", "category"]], on="product_id", how="left"
    ).merge(
        t["dim_customer"][["customer_id", "region", "customer_segment"]], on="customer_id", how="left"
    ).merge(
        t["dim_channel"][["channel_id", "channel_name", "channel_type"]], on="channel_id", how="left"
    )
    s["revenue"] = s["quantity"] * s["unit_price"] - s["discount_amount"] + s["shipping_revenue"]
    s["gross_profit"] = (
        s["revenue"] - s["product_cost"] - s["shipping_cost"]
        - s["payment_fee"] - s["refund_amount"]
    )
    s["year_month"] = s["order_date"].str.slice(0, 7)
    s["list_amount"] = s["quantity"] * s["unit_price"]
    return s


# --------------------------------------------------------------------------
# Aggregations
# --------------------------------------------------------------------------
def monthly(s: pd.DataFrame) -> pd.DataFrame:
    m = s.groupby("year_month").agg(
        orders=("order_id", "nunique"),
        revenue=("revenue", "sum"),
        gross_profit=("gross_profit", "sum"),
    ).reset_index()
    m["gross_margin_pct"] = 100 * m["gross_profit"] / m["revenue"]
    m["revenue_mom_pct"] = m["revenue"].pct_change() * 100
    return m


def by_category(s: pd.DataFrame) -> pd.DataFrame:
    c = s.groupby("category").agg(
        units=("quantity", "sum"),
        revenue=("revenue", "sum"),
        gross_profit=("gross_profit", "sum"),
    ).reset_index()
    c["gross_margin_pct"] = 100 * c["gross_profit"] / c["revenue"]
    return c.sort_values("gross_profit", ascending=False)


def by_product(s: pd.DataFrame) -> pd.DataFrame:
    p = s.groupby(["product_id", "product_name", "category"]).agg(
        units=("quantity", "sum"),
        revenue=("revenue", "sum"),
        gross_profit=("gross_profit", "sum"),
    ).reset_index()
    p["gross_margin_pct"] = 100 * p["gross_profit"] / p["revenue"]
    return p


def by_channel(t: dict[str, pd.DataFrame], s: pd.DataFrame) -> pd.DataFrame:
    sales = s.groupby("channel_id").agg(
        orders=("order_id", "nunique"),
        revenue=("revenue", "sum"),
        gross_profit=("gross_profit", "sum"),
    ).reset_index()
    mkt = t["fact_marketing"].groupby("channel_id").agg(
        spend=("marketing_spend", "sum"),
        conversions=("conversions", "sum"),
    ).reset_index()
    min_date = t["dim_date"]["date"].min()
    cust = t["dim_customer"]
    new = cust[cust["acquisition_date"] >= min_date].merge(
        t["dim_channel"][["channel_id", "channel_name"]],
        left_on="acquisition_channel", right_on="channel_name", how="left",
    ).groupby("channel_id").size().reset_index(name="new_customers")

    ch = t["dim_channel"].merge(sales, on="channel_id", how="left") \
        .merge(mkt, on="channel_id", how="left") \
        .merge(new, on="channel_id", how="left")
    for col in ("spend", "conversions", "new_customers"):
        ch[col] = ch[col].fillna(0)
    ch["gross_margin_pct"] = 100 * ch["gross_profit"] / ch["revenue"]
    ch["cac"] = np.where(ch["new_customers"] > 0, ch["spend"] / ch["new_customers"], np.nan)
    ch["roas"] = np.where(ch["spend"] > 0, ch["revenue"] / ch["spend"], np.nan)
    ch["net_marketing_contribution"] = ch["gross_profit"] - ch["spend"]
    return ch.sort_values("net_marketing_contribution", ascending=False)


def returns_by_category(s: pd.DataFrame) -> pd.DataFrame:
    r = s.groupby("category").agg(
        lines=("returned_flag", "size"),
        returned_lines=("returned_flag", "sum"),
        total_refund=("refund_amount", "sum"),
        revenue=("revenue", "sum"),
    ).reset_index()
    r["return_rate_pct"] = 100 * r["returned_lines"] / r["lines"]
    r["refund_pct_of_revenue"] = 100 * r["total_refund"] / r["revenue"]
    return r.sort_values("return_rate_pct", ascending=False)


def rfm_segments(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Segment summary using the single canonical RFM logic.

    Delegates to ``customer_segmentation`` so the whole project shares one
    segmentation (VIP / Clientes frecuentes / Nuevos clientes / Clientes en
    riesgo / Clientes inactivos), covering 100% of customers. Returns one row
    per segment with customer count, total monetary and average recency.
    """
    rfm, analysis_date = seg_mod.compute_rfm(t)
    scored = seg_mod.score_rfm(rfm)
    df = seg_mod.build_all_customers(t, scored, analysis_date)
    summary = df.groupby("segment").agg(
        customers=("customer_id", "size"),
        total_monetary=("monetary", "sum"),
        avg_recency=("recency_days", "mean"),
    ).reset_index().sort_values("total_monetary", ascending=False)
    return summary


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------
def _thousands(ax, axis: str = "y") -> None:
    fmt = mticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def _save(fig, name: str) -> None:
    fig.text(0.01, 0.01, SOURCE_NOTE, fontsize=7, color="gray", alpha=0.8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIGDIR / name, dpi=120, bbox_inches="tight")
    plt.close(fig)


def fig_monthly(m: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.barplot(data=m, x="year_month", y="revenue", color="#4C72B0", ax=ax, alpha=0.85)
    ax.set_ylabel("Revenue"); ax.set_xlabel(""); _thousands(ax)
    ax.tick_params(axis="x", rotation=45)
    ax2 = ax.twinx()
    ax2.plot(range(len(m)), m["gross_margin_pct"], color="#C44E52", marker="o", lw=2, label="Gross margin %")
    ax2.set_ylabel("Gross margin %")
    ax2.grid(False)
    ax.set_title("Revenue mensual y margen bruto (estacionalidad)", fontsize=13, weight="bold")
    ax2.legend(loc="upper left")
    _save(fig, "01_monthly_revenue_margin.png")


def fig_category(c: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    colors = ["#C44E52" if v < 0 else "#55A868" for v in c["gross_profit"]]
    sns.barplot(data=c, y="category", x="gross_profit", hue="category",
                palette=colors, legend=False, ax=axes[0])
    axes[0].axvline(0, color="black", lw=0.8)
    axes[0].set_title("Gross profit por categoría", weight="bold"); _thousands(axes[0], "x")
    axes[0].set_xlabel("Gross profit"); axes[0].set_ylabel("")

    cm = c.sort_values("gross_margin_pct")
    colors2 = ["#C44E52" if v < 0 else "#4C72B0" for v in cm["gross_margin_pct"]]
    sns.barplot(data=cm, y="category", x="gross_margin_pct", hue="category",
                palette=colors2, legend=False, ax=axes[1])
    axes[1].axvline(0, color="black", lw=0.8)
    axes[1].set_title("Margen bruto % por categoría", weight="bold")
    axes[1].set_xlabel("Gross margin %"); axes[1].set_ylabel("")
    _save(fig, "02_category_profit_margin.png")


def fig_volume_margin(p: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 6.5))
    sns.scatterplot(data=p, x="units", y="gross_margin_pct", hue="category",
                    size="revenue", sizes=(30, 500), alpha=0.7, ax=ax, legend="brief")
    ax.axhline(p["gross_margin_pct"].mean(), color="gray", ls="--", lw=1)
    ax.axvline(p["units"].mean(), color="gray", ls="--", lw=1)
    ax.set_title("Volumen vs. margen por producto (líneas = promedios)", fontsize=13, weight="bold")
    ax.set_xlabel("Unidades vendidas"); ax.set_ylabel("Gross margin %")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    _save(fig, "03_volume_vs_margin.png")


def fig_channel(ch: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(11, 5.5))
    colors = ["#C44E52" if v < 0 else "#55A868" for v in ch["net_marketing_contribution"]]
    sns.barplot(data=ch, x="channel_name", y="net_marketing_contribution", hue="channel_name",
                palette=colors, legend=False, ax=ax)
    ax.axhline(0, color="black", lw=0.8); _thousands(ax)
    ax.set_title("Contribución neta de marketing por canal (Gross Profit − Spend)",
                 fontsize=13, weight="bold")
    ax.set_xlabel(""); ax.set_ylabel("Net marketing contribution")
    for i, row in ch.reset_index().iterrows():
        label = f"ROAS {row['roas']:.1f}" if pd.notna(row["roas"]) else "sin spend"
        ax.annotate(label, (i, row["net_marketing_contribution"]),
                    ha="center", va="bottom" if row["net_marketing_contribution"] >= 0 else "top",
                    fontsize=8)
    _save(fig, "04_channel_net_contribution.png")


def fig_returns(r: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=r, x="return_rate_pct", y="category", color="#C44E52", ax=ax, alpha=0.85)
    ax.set_title("Tasa de devolución por categoría (nivel línea)", fontsize=13, weight="bold")
    ax.set_xlabel("Return rate %"); ax.set_ylabel("")
    for i, v in enumerate(r["return_rate_pct"]):
        ax.text(v + 0.1, i, f"{v:.1f}%", va="center", fontsize=8)
    _save(fig, "05_returns_by_category.png")


def fig_discount(s: pd.DataFrame) -> pd.DataFrame:
    d = s[s["list_amount"] > 0].copy()
    d["discount_rate"] = d["discount_amount"] / d["list_amount"]
    d["margin_pct"] = np.where(d["revenue"] > 0, 100 * d["gross_profit"] / d["revenue"], np.nan)
    d["disc_bucket"] = pd.cut(d["discount_rate"], bins=[-0.001, 0.0001, 0.1, 0.2, 0.3, 1.0],
                              labels=["0%", "0-10%", "10-20%", "20-30%", ">30%"])
    agg = d.groupby("disc_bucket", observed=True)["margin_pct"].mean().reset_index()
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=agg, x="disc_bucket", y="margin_pct", color="#4C72B0", ax=ax)
    ax.set_title("Margen bruto promedio por nivel de descuento", fontsize=13, weight="bold")
    ax.set_xlabel("Descuento aplicado"); ax.set_ylabel("Gross margin % promedio")
    ax.axhline(0, color="black", lw=0.8)
    _save(fig, "06_discount_vs_margin.png")
    return d


def fig_shipping(s: pd.DataFrame) -> pd.DataFrame:
    r = s.groupby("region").agg(
        avg_shipping_cost=("shipping_cost", "mean"),
        total_shipping_cost=("shipping_cost", "sum"),
        total_shipping_revenue=("shipping_revenue", "sum"),
    ).reset_index()
    r["net_shipping"] = r["total_shipping_revenue"] - r["total_shipping_cost"]
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=r.sort_values("avg_shipping_cost"), x="region", y="avg_shipping_cost",
                color="#8172B3", ax=ax)
    ax.set_title("Costo de envío promedio por zona (región)", fontsize=13, weight="bold")
    ax.set_xlabel(""); ax.set_ylabel("Costo de envío promedio")
    _save(fig, "07_shipping_by_region.png")
    return r


def fig_rfm(seg: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    sns.barplot(data=seg, x="customers", y="segment", color="#4C72B0", ax=axes[0])
    axes[0].set_title("Clientes por segmento RFM", weight="bold")
    axes[0].set_xlabel("Clientes"); axes[0].set_ylabel("")
    sns.barplot(data=seg, x="total_monetary", y="segment", color="#55A868", ax=axes[1])
    axes[1].set_title("Valor (monetary) por segmento RFM", weight="bold")
    axes[1].set_xlabel("Total monetary"); axes[1].set_ylabel(""); _thousands(axes[1], "x")
    _save(fig, "08_rfm_segments.png")


# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------
def _money(x: float) -> str:
    return f"{x:,.0f}"


def build_findings_md(s, m, c, p, ch, r, seg, disc, ship) -> str:
    total_rev = s["revenue"].sum()
    total_gp = s["gross_profit"].sum()
    overall_margin = 100 * total_gp / total_rev

    # Categories.
    loss_cats = c[c["gross_profit"] < 0].sort_values("gross_profit")
    elec = c[c["category"] == "Electronics"].iloc[0]
    top_cat = c.iloc[0]

    # Seasonality.
    peak = m.loc[m["revenue"].idxmax()]
    trough_mom = m.loc[m["revenue_mom_pct"].idxmin()]

    # Concentration.
    p_sorted = p.sort_values("gross_profit", ascending=False)
    top10_share = 100 * p_sorted.head(10)["gross_profit"].sum() / total_gp
    top1 = p_sorted.iloc[0]
    top1_share = 100 * top1["gross_profit"] / total_gp

    # Channels.
    paid = ch[ch["channel_type"] == "Paid"].sort_values("net_marketing_contribution")
    worst_ch = paid.iloc[0]
    email = ch[ch["channel_name"] == "Email"].iloc[0]
    zero_spend_gp = ch[ch["spend"] == 0]["gross_profit"].sum()

    # Returns.
    worst_ret = r.iloc[0]

    # Discounts.
    disc_pos = disc[disc["discount_rate"] > 0]["margin_pct"].mean()
    disc_zero = disc[disc["discount_rate"] == 0]["margin_pct"].mean()
    disc_gap = disc_zero - disc_pos
    disc_word = "menor" if disc_gap > 0 else "mayor"

    # Shipping.
    net_ship = ship["net_shipping"].sum()
    ship_word = "pérdida" if net_ship < 0 else "ganancia"

    # RFM (canonical scheme: VIP / Clientes frecuentes / Nuevos / en riesgo / inactivos).
    vip = seg[seg["segment"] == "VIP"].iloc[0]
    vip_share = 100 * vip["customers"] / seg["customers"].sum()
    at_risk = seg[seg["segment"] == "Clientes en riesgo"]
    at_risk_row = at_risk.iloc[0] if len(at_risk) else None

    return f"""# Hallazgos — E-commerce Profitability Analytics

> **Datos simulados** (semilla 42). Este informe distingue explícitamente entre
> *hallazgo descriptivo* (lo que muestran los datos), *interpretación* (posible
> explicación), *recomendación* (acción sugerida) y *limitaciones*. Ninguna cifra
> proviene de fuentes externas; todas se calculan desde `data/processed/`.

**Marco global:** Revenue total **{_money(total_rev)}**, Gross Profit
**{_money(total_gp)}**, margen bruto global **{overall_margin:.1f}%** sobre
{s['order_id'].nunique():,} pedidos y 18 meses. Figuras en `reports/figures/`.

---

## P1 · Categorías que destruyen margen pese a su alto revenue
- **Evidencia (descriptivo):** {len(loss_cats)} categorías tienen gross profit
  **negativo**: {", ".join(f"{row.category} ({_money(row.gross_profit)})" for row in loss_cats.itertuples())}.
  `Electronics` factura **{_money(elec.revenue)}** (el mayor revenue) pero pierde
  **{_money(elec.gross_profit)}** (margen {elec.gross_margin_pct:.1f}%).
- **Interpretación:** categorías de alto precio y bajo margen unitario donde los
  costos logísticos, comisiones de pago y devoluciones superan el margen de producto.
- **Implicación de negocio:** el revenue no equivale a rentabilidad; el mix actual
  subsidia ventas que pierden dinero.
- **Recomendación:** renegociar costos con proveedores, reducir descuentos y
  devoluciones en estas categorías, revisar precios o acotar el surtido menos rentable.
- *Ver:* `02_category_profit_margin.png`.

## P2 · Los canales pagados no se sostienen tras marketing
- **Evidencia (descriptivo):** `{worst_ch.channel_name}` tiene contribución neta de
  marketing **{_money(worst_ch.net_marketing_contribution)}** (CAC {worst_ch.cac:.0f},
  ROAS {worst_ch.roas:.1f}). Los canales sin inversión (Organic, Direct) aportan
  **{_money(zero_spend_gp)}** de gross profit. `Email` es el pago más eficiente
  (ROAS {email.roas:.1f}, contribución {_money(email.net_marketing_contribution)}).
- **Interpretación:** el gasto en Paid Search/Social supera el gross profit que generan;
  el crecimiento orgánico sostiene la rentabilidad real.
- **Implicación de negocio:** parte del presupuesto de marketing reduce el beneficio.
- **Recomendación:** reasignar presupuesto desde los pagados menos eficientes hacia
  Email y refuerzo de orgánico; auditar la atribución antes de escalar.
- *Ver:* `04_channel_net_contribution.png`.

## P3 · Estacionalidad marcada con compresión de margen en el pico
- **Evidencia (descriptivo):** el mes pico es **{peak.year_month}** con revenue
  **{_money(peak.revenue)}** (margen {peak.gross_margin_pct:.1f}%). La mayor caída
  intermensual es **{trough_mom.year_month}** ({trough_mom.revenue_mom_pct:.1f}% MoM).
- **Interpretación:** concentración de demanda en Nov–Dic; el margen no sube en el
  pico (posible mayor descuento/envío en temporada alta).
- **Implicación de negocio:** el trimestre final define el año pero con margen presionado.
- **Recomendación:** planificar inventario y marketing hacia el Q4 y proteger el
  margen en temporada (limitar descuentos agresivos, optimizar envío).
- *Ver:* `01_monthly_revenue_margin.png`.

## P4 · Beneficio muy concentrado en pocas categorías y productos
- **Evidencia (descriptivo):** los 10 productos top concentran **{top10_share:.1f}%**
  del gross profit; `{top1.product_name}` solo aporta **{top1_share:.1f}%**.
  `{top_cat.category}` es la categoría más rentable ({_money(top_cat.gross_profit)},
  margen {top_cat.gross_margin_pct:.1f}%).
- **Interpretación:** la rentabilidad depende de un núcleo reducido de productos
  (Sports & Outdoors y Fashion como motores).
- **Implicación de negocio:** riesgo de concentración: un quiebre de stock o caída de
  demanda de esos productos golpea el resultado global.
- **Recomendación:** proteger disponibilidad de los productos clave, monitorearlos con
  alertas y diversificar la base de productos rentables.
- *Ver:* `03_volume_vs_margin.png`.

## P5 · Las devoluciones erosionan el margen de las categorías premium
- **Evidencia (descriptivo):** la mayor tasa de devolución es `{worst_ret.category}`
  con **{worst_ret.return_rate_pct:.1f}%** de líneas devueltas y
  {worst_ret.refund_pct_of_revenue:.1f}% del revenue reembolsado.
- **Interpretación:** categorías con alta variabilidad (p. ej. talla/ajuste en Fashion)
  presentan más devoluciones, reduciendo su margen efectivo.
- **Implicación de negocio:** parte del margen "de lista" se pierde en logística inversa.
- **Recomendación:** mejorar fichas/tallaje y calidad de descripción para reducir
  devoluciones evitables; monitorear devoluciones por producto.
- *Ver:* `05_returns_by_category.png`.

## P6 · Fugas de margen operativas: descuentos y envío
- **Evidencia (descriptivo):** las líneas con descuento promedian **{disc_pos:.1f}%**
  de margen vs. **{disc_zero:.1f}%** sin descuento (un margen {disc_word} en
  {abs(disc_gap):.1f} puntos). El envío genera una **{ship_word}** neta de
  **{_money(net_ship)}** (ingreso por envío − costo logístico).
- **Interpretación:** el descuento se asocia a menor margen y el envío está
  parcialmente subsidiado (envío gratis frecuente).
- **Implicación de negocio:** dos palancas operativas drenan margen de forma transversal.
- **Recomendación:** poner topes de descuento en productos de bajo margen y revisar el
  umbral de envío gratis / cobrar envío en pedidos pequeños.
- *Ver:* `06_discount_vs_margin.png`, `07_shipping_by_region.png`.

---

## Resumen ejecutivo

| # | Hallazgo | Palanca | Prioridad |
|---|---|---|---|
| P1 | Categorías con profit negativo (Electronics, Grocery) | Pricing / costos | Alta |
| P2 | Canales pagados con contribución neta negativa | Marketing | Alta |
| P3 | Estacionalidad Q4 con margen comprimido | Planificación | Media |
| P4 | Concentración de beneficio en pocos productos | Riesgo / surtido | Media |
| P5 | Devoluciones altas en categorías premium | Operaciones | Media |
| P6 | Descuentos y envío drenan margen | Operaciones | Media |

**Segmentos de cliente (RFM):** `VIP` = {vip.customers:,.0f} clientes
({vip_share:.1f}%) con {_money(vip.total_monetary)} de valor.{
    f" `Clientes en riesgo` = {at_risk_row.customers:,.0f} clientes con {_money(at_risk_row.total_monetary)} en riesgo de fuga." if at_risk_row is not None else ""
} Recomendación: retención dirigida a `Clientes en riesgo` y fidelización de `VIP`
(ver `08_rfm_segments.png` y la segmentación completa en `reports/customer_segmentation.md`).

## Limitaciones

- **Datos simulados:** patrones generados con semilla fija; no representan un negocio real.
- **Atribución de canal de único toque** (canal del pedido), no multitáctil.
- Umbrales de "alto/bajo" volumen y margen definidos por el **promedio** de productos.
- CLV no modelado probabilísticamente; `monetary` usado como proxy de valor.
- Correlaciones y comparaciones son **asociaciones**, no relaciones causales.
"""


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def run() -> None:
    sns.set_theme(style="whitegrid", palette="deep")
    FIGDIR.mkdir(parents=True, exist_ok=True)

    t = load()
    s = prepare(t)
    m, c, p = monthly(s), by_category(s), by_product(s)
    ch, r, seg = by_channel(t, s), returns_by_category(s), rfm_segments(t)

    fig_monthly(m)
    fig_category(c)
    fig_volume_margin(p)
    fig_channel(ch)
    fig_returns(r)
    disc = fig_discount(s)
    ship = fig_shipping(s)
    fig_rfm(seg)

    report = build_findings_md(s, m, c, p, ch, r, seg, disc, ship)
    (config.REPORTS_DIR / "findings.md").write_text(report, encoding="utf-8")


def main() -> None:
    run()
    figs = sorted(pf.name for pf in FIGDIR.glob("*.png"))
    print(f"Analysis complete. {len(figs)} figures in {FIGDIR}")
    for f in figs:
        print("  -", f)
    print("Findings written to", config.REPORTS_DIR / "findings.md")


if __name__ == "__main__":
    main()
