# Supuestos

> ⚠️ **Datos simulados — proyecto demostrativo.** Este registro documenta las
> decisiones de modelado adoptadas. Ninguna cifra proviene de una empresa real.

Registro de los supuestos adoptados en el proyecto, organizados por ámbito. La
trazabilidad de cada parámetro está en [`src/config.py`](../src/config.py).

## 1. Datos

- Los datos son **simulados** con **semilla aleatoria fija** (`RANDOM_SEED = 42`),
  de modo que el dataset es idéntico en cada ejecución.
- El periodo cubre **18 meses** (2024-01-01 a 2025-06-30), cumpliendo el mínimo de 18.
- Volumen: **3,000** clientes, **60** productos, **20,000** pedidos (32,083 líneas),
  **8** categorías y **6** canales de adquisición — dentro de los rangos definidos.
- Se inyectan **nulos e inconsistencias controladas** (~1%) de forma deliberada para
  poder probar las validaciones de calidad; tras la limpieza, los 15 chequeos dan 0 errores.
- Un **25%** de los clientes se adquiere antes de la ventana de observación (base
  existente), para permitir el cálculo de recurrencia y RFM desde el primer mes.

## 2. Negocio (definiciones de indicadores)

- **Revenue** = `quantity × unit_price − discount_amount + shipping_revenue`.
- **Product Cost** = `quantity × unit_cost`.
- **Gross Profit** = `Revenue − Product Cost − Shipping Cost − Payment Fee − Refund Amount`.
  El margen es **bruto** e incluye logística, comisiones de pago y devoluciones (por eso
  es más bajo que un margen de producto puro).
- **Gross Margin %** = `Gross Profit / Revenue`.
- **CAC** = `Marketing Spend / New Customers Acquired` (solo canales con inversión).
- **ROAS** = `Revenue atribuido al canal / Marketing Spend`.
- **Net Marketing Contribution** = `Gross Profit − Marketing Spend`.
- **Return Rate** se reporta a **nivel de línea** (líneas devueltas / líneas totales).

## 3. Atribución y segmentación

- **Atribución de canal de único toque:** cada pedido se asigna al canal registrado en
  la venta; no es un modelo multitáctil.
- Los canales **Organic Search** y **Direct** no tienen inversión de marketing, por lo
  que su CAC y ROAS no se calculan (contribución neta = gross profit).
- **RFM** con **fecha de análisis** = último pedido del dataset (2025-06-30); scores 1–5
  por quintiles de rango. Base = 2,443 clientes con al menos una compra.
- Umbrales de segmento RFM (≥3, ≥4, ≤2) son una **convención de negocio**, no óptimos
  estadísticos.
- Umbrales de "alto/bajo" volumen y margen definidos respecto al **promedio** de productos.

## 4. Técnicos

- Base de datos analítica en **SQLite** (portátil, sin servidor).
- **Moneda única**, sin conversión de divisas ni inflación.
- Geografía, marcas, proveedores y nombres de producto son **ficticios**.
- El alcance es **analítico**, no transaccional (no hay concurrencia ni integridad de producción).
