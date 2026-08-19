# Especificación del Dashboard — E-commerce Profitability Analytics

> ⚠️ **Este documento es una ESPECIFICACIÓN.** El archivo `.pbix` **no** está
> construido; aquí se define qué debe contener el dashboard para poder
> implementarlo de forma reproducible. Datos **simulados**.

Modelo y medidas: ver [`data_dictionary.md`](data_dictionary.md) y
[`dax_measures.md`](dax_measures.md).

---

## Paleta de colores recomendada

| Rol | Hex | Uso |
|---|---|---|
| Primario | `#4C72B0` | Revenue, barras/series principales |
| Positivo | `#55A868` | Gross profit, valores favorables, VIP |
| Negativo | `#C44E52` | Pérdidas, márgenes negativos, alertas, inactivos |
| Acento | `#8172B3` | Series secundarias, "Nuevos" |
| Advertencia | `#DD8452` | "En riesgo", umbrales |
| Neutro | `#4C4C4C` / `#BAB0AC` | Texto, ejes, fondos |

Fondo claro, tipografía Segoe UI, KPIs en tarjetas con formato de moneda y %.
Regla de color condicional: verde ≥ 0, rojo < 0 en profit/margen/contribución.

---

## Página 1 · Executive Overview

**Objetivo:** foto ejecutiva de negocio en un vistazo.

- **KPIs (tarjetas):** `Revenue`, `Gross Profit`, `Gross Margin %`, `Orders`,
  `Average Order Value`, `Marketing Spend`, `ROAS`.
- **Visualizaciones:**
  - Gráfico combinado (columnas + línea): columnas `Revenue` por mes + línea
    `Gross Margin %`. Eje: `dim_date[month]` (jerarquía año-mes).
  - Línea: `Revenue Growth %` y `Gross Profit Growth %` por mes.
  - Barras: `Gross Profit` por `dim_product[category]`.
- **Campos clave:** medidas del grupo overview; eje temporal `dim_date`.
- **Filtros (slicers):** `dim_date[year/month]`, `dim_product[category]`, `dim_channel[channel_name]`.
- **Interacciones:** los slicers filtran toda la página; al seleccionar un mes en el
  combinado se resaltan (cross-highlight) las barras de categoría.
- **Colores:** Revenue `#4C72B0`, margen/línea `#C44E52`, profit `#55A868`.

## Página 2 · Product Profitability

**Objetivo:** dónde se gana y se pierde margen por categoría/producto.

- **Visualizaciones:**
  - Barras horizontales: `Revenue` y `Gross Profit` por `category` (color condicional).
  - **Matriz volumen vs. margen** (scatter): eje X `Units Sold`, eje Y `Gross Margin %`,
    tamaño `Revenue`, leyenda `category`, detalle `dim_product[product_name]`.
    Líneas de referencia en los promedios.
  - Tabla de productos: `product_name`, `category`, `Units Sold`, `Revenue`,
    `Gross Profit`, `Gross Margin %` (barras de datos condicionales).
  - Barras: Top 10 productos por `Gross Profit`.
- **Filtros:** `category`, `brand`, `active_flag`, rango de fecha.
- **Interacciones:** clic en categoría (barras) filtra el scatter y la tabla.
- **Colores:** margen negativo `#C44E52`; cuadrante "alto volumen/bajo margen" resaltado.

## Página 3 · Marketing Performance

**Objetivo:** eficiencia de canales y campañas.

- **KPIs:** `Marketing Spend`, `Revenue`, `ROAS`, `CAC`, `Net Marketing Contribution`, conversiones.
- **Visualizaciones:**
  - Barras: `Net Marketing Contribution` por `channel_name` (color condicional ±).
  - Combinado: `Marketing Spend` (columnas) vs `ROAS` (línea) por canal.
  - Dispersión: `CAC` (X) vs `ROAS` (Y) por canal, tamaño `New Customers`.
  - Tabla de campañas: `campaign_name`, spend, `impressions`, `clicks`,
    `conversions`, cost per conversion.
- **Campos:** `dim_channel`, `fact_marketing`, medidas de marketing.
- **Filtros:** `channel_type`, `channel_name`, fecha.
- **Interacciones:** seleccionar canal filtra campañas y KPIs.
- **Colores:** contribución negativa `#C44E52`, positiva `#55A868`, spend `#4C72B0`.

## Página 4 · Customer Analytics

**Objetivo:** valor y riesgo de la base de clientes (RFM).

- **KPIs:** `Customers With Orders`, `Repeat Purchase Rate`, `Revenue per Customer`, `CLV Approx`.
- **Visualizaciones:**
  - Barras: clientes por `customer_rfm[segment]` y valor (`monetary`) por segmento.
  - Dispersión RFM: `recency_days` (X) vs `frequency` (Y), tamaño `monetary`, leyenda `segment`.
  - Tabla: clientes `En riesgo` (mayor `monetary`) para acción comercial.
  - Tarjetas: nº de VIP y % de valor que representan.
- **Campos:** tabla `customer_rfm` (relación 1:1 con `dim_customer`).
- **Filtros:** `segment`, `region`, `acquisition_channel`.
- **Interacciones:** seleccionar segmento filtra la dispersión y la tabla.
- **Colores:** VIP `#55A868`, Frecuentes `#4C72B0`, Nuevos `#8172B3`,
  En riesgo `#DD8452`, Inactivos `#C44E52`.

## Página 5 · Operational Insights

**Objetivo:** fugas operativas y oportunidades priorizadas.

- **Visualizaciones:**
  - Barras: `Return Rate` por `category` (+ `Refund Amount`).
  - Barras: costo de envío promedio por `region`; tarjeta de envío neto (rev − costo).
  - Combinado: `Average Discount %` vs `Gross Margin %` por nivel de descuento.
  - Tabla de alertas: productos con margen negativo o alta devolución.
  - Panel "Oportunidades priorizadas" (cuadro de texto con acciones de `findings.md`).
- **Filtros:** `category`, `region`, fecha.
- **Interacciones:** clic en categoría/región filtra el resto.
- **Colores:** alertas `#C44E52`, envío `#8172B3`, descuento `#DD8452`.

---

## Navegación e interacciones globales

- Barra de navegación entre las 5 páginas (botones).
- Slicers sincronizados de **fecha** y **categoría** entre páginas (Sincronizar segmentaciones).
- Tooltips con medidas clave (Revenue, Gross Profit, Margin %).
- "Edit interactions": los KPIs (tarjetas) en modo *no filtrar* al hacer cross-highlight
  para que sigan mostrando el total del contexto de slicers.

---

## Conexión de datos

El repositorio **no** incluye el `.pbix` ni los CSV (regenerables). Primero
reconstruir la capa de datos:

```bash
python -m src.generate_data        # data/raw/
python -m src.clean_data           # data/processed/
python -m src.load_database        # database/ecommerce.db
python -m src.customer_segmentation  # data/processed/customer_rfm.csv
```

### Opción A (recomendada) — CSV procesados

Portátil y sin drivers adicionales.

1. Power BI Desktop → **Obtener datos → Carpeta** → `data/processed/`
   (o **Texto/CSV** archivo por archivo, incluido `customer_rfm.csv`).
2. Cargar las 6 tablas del modelo + `customer_rfm`.
3. En **Vista de modelo**, crear las relaciones (todas 1:\*, filtro simple):
   - `dim_date[date]` → `fact_sales[order_date]` (activa)
   - `dim_date[date]` → `fact_marketing[date]` (activa)
   - `dim_date[date]` → `dim_customer[acquisition_date]` (**inactiva**, para CAC)
   - `dim_product[product_id]` → `fact_sales[product_id]`
   - `dim_customer[customer_id]` → `fact_sales[customer_id]`
   - `dim_channel[channel_id]` → `fact_sales[channel_id]` y `fact_marketing[channel_id]`
   - `dim_customer[customer_id]` → `customer_rfm[customer_id]` (1:1)
4. **Marcar `dim_date` como tabla de fechas** con `dim_date[date]`.
5. Ajustar tipos: fechas como *Date*, montos como *Decimal*, ids como *Text*.
6. Crear la tabla `_Measures` y pegar las medidas de `dax_measures.md`.

### Opción B — SQLite (`database/ecommerce.db`)

Power BI **no** trae conector nativo de SQLite; se requiere un driver ODBC.

1. Instalar el **SQLite ODBC Driver** (p. ej. el de Ch. Werner) y crear un DSN
   apuntando a `database/ecommerce.db`.
2. Power BI → **Obtener datos → ODBC** → seleccionar el DSN → elegir las tablas.
3. Crear relaciones y marcar tabla de fechas igual que en la Opción A.
   *Ventaja:* las claves, índices y `CHECK` ya están definidos en el esquema.

> Recomendación: usar la **Opción A** para máxima reproducibilidad y portabilidad;
> la Opción B es útil si se prefiere una única fuente relacional con integridad.

---

## Estado

Preparación **completa** de la especificación (páginas, visuales, campos, filtros,
interacciones, colores) y de la capa DAX. **El dashboard `.pbix` aún no se ha
construido**: este documento permite implementarlo, pero no debe presentarse como
un tablero ya finalizado.
