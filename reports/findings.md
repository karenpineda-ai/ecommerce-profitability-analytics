# Hallazgos — E-commerce Profitability Analytics

> **Datos simulados** (semilla 42). Este informe distingue explícitamente entre
> *hallazgo descriptivo* (lo que muestran los datos), *interpretación* (posible
> explicación), *recomendación* (acción sugerida) y *limitaciones*. Ninguna cifra
> proviene de fuentes externas; todas se calculan desde `data/processed/`.

**Marco global:** Revenue total **12,417,781**, Gross Profit
**1,111,339**, margen bruto global **8.9%** sobre
20,000 pedidos y 18 meses. Figuras en `reports/figures/`.

---

## P1 · Categorías que destruyen margen pese a su alto revenue
- **Evidencia (descriptivo):** 2 categorías tienen gross profit
  **negativo**: Electronics (-159,730), Grocery (-8,721).
  `Electronics` factura **7,293,945** (el mayor revenue) pero pierde
  **-159,730** (margen -2.2%).
- **Interpretación:** categorías de alto precio y bajo margen unitario donde los
  costos logísticos, comisiones de pago y devoluciones superan el margen de producto.
- **Implicación de negocio:** el revenue no equivale a rentabilidad; el mix actual
  subsidia ventas que pierden dinero.
- **Recomendación:** renegociar costos con proveedores, reducir descuentos y
  devoluciones en estas categorías, revisar precios o acotar el surtido menos rentable.
- *Ver:* `02_category_profit_margin.png`.

## P2 · Los canales pagados no se sostienen tras marketing
- **Evidencia (descriptivo):** `Paid Search` tiene contribución neta de
  marketing **-262,342** (CAC 1102,
  ROAS 4.9). Los canales sin inversión (Organic, Direct) aportan
  **468,791** de gross profit. `Email` es el pago más eficiente
  (ROAS 23.6, contribución 67,135).
- **Interpretación:** el gasto en Paid Search/Social supera el gross profit que generan;
  el crecimiento orgánico sostiene la rentabilidad real.
- **Implicación de negocio:** parte del presupuesto de marketing reduce el beneficio.
- **Recomendación:** reasignar presupuesto desde los pagados menos eficientes hacia
  Email y refuerzo de orgánico; auditar la atribución antes de escalar.
- *Ver:* `04_channel_net_contribution.png`.

## P3 · Estacionalidad marcada con compresión de margen en el pico
- **Evidencia (descriptivo):** el mes pico es **2024-12** con revenue
  **1,044,498** (margen 8.9%). La mayor caída
  intermensual es **2025-01** (-39.9% MoM).
- **Interpretación:** concentración de demanda en Nov–Dic; el margen no sube en el
  pico (posible mayor descuento/envío en temporada alta).
- **Implicación de negocio:** el trimestre final define el año pero con margen presionado.
- **Recomendación:** planificar inventario y marketing hacia el Q4 y proteger el
  margen en temporada (limitar descuentos agresivos, optimizar envío).
- *Ver:* `01_monthly_revenue_margin.png`.

## P4 · Beneficio muy concentrado en pocas categorías y productos
- **Evidencia (descriptivo):** los 10 productos top concentran **75.1%**
  del gross profit; `Cobalt Sports Max` solo aporta **26.3%**.
  `Sports & Outdoors` es la categoría más rentable (512,843,
  margen 30.4%).
- **Interpretación:** la rentabilidad depende de un núcleo reducido de productos
  (Sports & Outdoors y Fashion como motores).
- **Implicación de negocio:** riesgo de concentración: un quiebre de stock o caída de
  demanda de esos productos golpea el resultado global.
- **Recomendación:** proteger disponibilidad de los productos clave, monitorearlos con
  alertas y diversificar la base de productos rentables.
- *Ver:* `03_volume_vs_margin.png`.

## P5 · Las devoluciones erosionan el margen de las categorías premium
- **Evidencia (descriptivo):** la mayor tasa de devolución es `Fashion`
  con **15.5%** de líneas devueltas y
  15.7% del revenue reembolsado.
- **Interpretación:** categorías con alta variabilidad (p. ej. talla/ajuste en Fashion)
  presentan más devoluciones, reduciendo su margen efectivo.
- **Implicación de negocio:** parte del margen "de lista" se pierde en logística inversa.
- **Recomendación:** mejorar fichas/tallaje y calidad de descripción para reducir
  devoluciones evitables; monitorear devoluciones por producto.
- *Ver:* `05_returns_by_category.png`.

## P6 · Fugas de margen operativas: descuentos y envío
- **Evidencia (descriptivo):** las líneas con descuento promedian **8.7%**
  de margen vs. **22.3%** sin descuento (un margen menor en
  13.7 puntos). El envío genera una **pérdida** neta de
  **-40,489** (ingreso por envío − costo logístico).
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

**Segmentos de cliente (RFM):** `VIP` = 619 clientes
(20.6%) con 6,996,479 de valor. `Clientes en riesgo` = 487 clientes con 2,200,527 en riesgo de fuga. Recomendación: retención dirigida a `Clientes en riesgo` y fidelización de `VIP`
(ver `08_rfm_segments.png` y la segmentación completa en `reports/customer_segmentation.md`).

## Limitaciones

- **Datos simulados:** patrones generados con semilla fija; no representan un negocio real.
- **Atribución de canal de único toque** (canal del pedido), no multitáctil.
- Umbrales de "alto/bajo" volumen y margen definidos por el **promedio** de productos.
- CLV no modelado probabilísticamente; `monetary` usado como proxy de valor.
- Correlaciones y comparaciones son **asociaciones**, no relaciones causales.
