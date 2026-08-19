# Diccionario de Datos — Modelo Analítico

> Datos **simulados** (semilla `42`). Base: `database/ecommerce.db` (SQLite),
> generada por `src/load_database.py` a partir de `data/processed/`.

## Modelo estrella

```text
                 ┌──────────────┐
                 │  dim_date    │
                 └──────┬───────┘
                        │ date
   ┌──────────────┐     │      ┌──────────────┐
   │ dim_customer │◄──┐ │ ┌──►│ dim_product  │
   └──────────────┘   │ │ │    └──────────────┘
                    ┌──┴─┴─┴───┐
                    │ fact_sales│
                    └──┬───────┬┘
                       │       │ channel_id
              ┌────────▼──┐    │
              │dim_channel│◄───┘
              └────┬──────┘
                   │ channel_id / date
             ┌─────▼────────┐
             │fact_marketing│
             └──────────────┘
```

- **Hechos:** `fact_sales` (grano = línea de pedido), `fact_marketing` (grano = canal-día-campaña).
- **Dimensiones:** `dim_date`, `dim_product`, `dim_customer`, `dim_channel`.
- **Relaciones (Power BI):** de la dimensión (1) hacia el hecho (\*), dirección de filtro simple.

| Relación | Desde | Hacia | Cardinalidad |
|---|---|---|---|
| Fecha de venta | `dim_date[date]` | `fact_sales[order_date]` | 1:\* |
| Fecha marketing | `dim_date[date]` | `fact_marketing[date]` | 1:\* |
| Producto | `dim_product[product_id]` | `fact_sales[product_id]` | 1:\* |
| Cliente | `dim_customer[customer_id]` | `fact_sales[customer_id]` | 1:\* |
| Canal (ventas) | `dim_channel[channel_id]` | `fact_sales[channel_id]` | 1:\* |
| Canal (marketing) | `dim_channel[channel_id]` | `fact_marketing[channel_id]` | 1:\* |

---

## dim_date

Calendario diario. PK: `date_key`. `date` es UNIQUE y sirve de destino de FK.

| Columna | Tipo | Descripción |
|---|---|---|
| `date_key` | INTEGER (PK) | Fecha en formato `YYYYMMDD`. |
| `date` | TEXT (UNIQUE) | Fecha ISO `YYYY-MM-DD`. |
| `year` | INTEGER | Año. |
| `quarter` | INTEGER | Trimestre (1–4). |
| `month` | INTEGER | Mes (1–12). |
| `month_name` | TEXT | Nombre del mes en inglés. |
| `week` | INTEGER | Semana ISO. |
| `day_of_week` | TEXT | Día de la semana. |

## dim_product

Catálogo de productos. PK: `product_id`.

| Columna | Tipo | Descripción |
|---|---|---|
| `product_id` | TEXT (PK) | Identificador `P####`. |
| `product_name` | TEXT | Nombre comercial. |
| `category` | TEXT | Categoría (8 valores). |
| `subcategory` | TEXT | Subcategoría (`Unknown` si faltaba). |
| `brand` | TEXT | Marca (`Unknown` si faltaba). |
| `unit_cost` | REAL ≥ 0 | Costo unitario. |
| `list_price` | REAL ≥ 0 | Precio de lista. |
| `supplier` | TEXT | Proveedor. |
| `active_flag` | INTEGER (0/1) | Producto activo. |

## dim_customer

Clientes. PK: `customer_id`.

| Columna | Tipo | Descripción |
|---|---|---|
| `customer_id` | TEXT (PK) | Identificador `C#####`. |
| `customer_segment` | TEXT | `New` / `Regular` / `VIP`. |
| `city` | TEXT | Ciudad (`Unknown` si faltaba). |
| `region` | TEXT | Región (`Unknown` si faltaba). |
| `acquisition_date` | TEXT | Fecha de adquisición ISO. |
| `acquisition_channel` | TEXT | Canal de adquisición. |

## dim_channel

Canales de adquisición / marketing. PK: `channel_id`.

| Columna | Tipo | Descripción |
|---|---|---|
| `channel_id` | INTEGER (PK) | Identificador 1–6. |
| `channel_name` | TEXT (UNIQUE) | Nombre del canal. |
| `channel_type` | TEXT | `Organic` / `Paid` / `Owned` / `Referral` / `Direct`. |

## fact_sales

Ventas a nivel de línea de pedido. PK surrogate: `sale_id`.

| Columna | Tipo | Descripción |
|---|---|---|
| `sale_id` | INTEGER (PK, auto) | Clave surrogate de la línea. |
| `order_id` | TEXT | Agrupa líneas de un mismo pedido. |
| `order_date` | TEXT → `dim_date[date]` | Fecha del pedido. |
| `customer_id` | TEXT → `dim_customer` | Cliente. |
| `product_id` | TEXT → `dim_product` | Producto. |
| `channel_id` | INTEGER → `dim_channel` | Canal de origen. |
| `quantity` | INTEGER > 0 | Unidades. |
| `unit_price` | REAL ≥ 0 | Precio unitario de venta. |
| `discount_amount` | REAL ≥ 0 | Descuento total de la línea. |
| `shipping_revenue` | REAL ≥ 0 | Ingreso por envío cobrado. |
| `product_cost` | REAL ≥ 0 | Costo total (`quantity × unit_cost`). |
| `shipping_cost` | REAL ≥ 0 | Costo logístico. |
| `payment_fee` | REAL ≥ 0 | Comisión de pago. |
| `returned_flag` | INTEGER (0/1) | Línea devuelta. |
| `refund_amount` | REAL ≥ 0 | Monto reembolsado. |

**Métricas derivadas** (ver `CLAUDE.md`):
`Revenue = quantity*unit_price - discount_amount + shipping_revenue` ·
`Gross Profit = Revenue - product_cost - shipping_cost - payment_fee - refund_amount`.

## fact_marketing

Actividad de marketing por canal y día. PK surrogate: `marketing_id`.

| Columna | Tipo | Descripción |
|---|---|---|
| `marketing_id` | INTEGER (PK, auto) | Clave surrogate. |
| `date` | TEXT → `dim_date[date]` | Día. |
| `channel_id` | INTEGER → `dim_channel` | Canal. |
| `campaign_name` | TEXT | Campaña. |
| `impressions` | INTEGER ≥ 0 | Impresiones. |
| `clicks` | INTEGER ≥ 0 | Clics. |
| `leads` | INTEGER ≥ 0 | Leads. |
| `conversions` | INTEGER ≥ 0 | Conversiones. |
| `marketing_spend` | REAL ≥ 0 | Inversión. |

> Solo los canales con inversión (Paid Search, Social Ads, Email, Referral)
> aparecen en `fact_marketing`.

---

## Índices

`fact_sales`: `order_id`, `customer_id`, `product_id`, `channel_id`, `order_date`.
`fact_marketing`: `channel_id`, `date`. `dim_customer`: `acquisition_channel`.
`dim_product`: `category`.

## Restricciones de integridad

- PK en todas las dimensiones y `sale_id` / `marketing_id` en los hechos.
- FKs de los hechos hacia todas las dimensiones (con `PRAGMA foreign_keys = ON`).
- `CHECK` de no-negatividad en montos, `quantity > 0`, y flags binarios (0/1).

---

## customer_rfm (tabla analítica auxiliar)

Salida de `src/customer_segmentation.py` (`data/processed/customer_rfm.csv`), una
fila por cliente. Se relaciona **1:1** con `dim_customer[customer_id]` para filtrar
todo el modelo por segmento RFM. Ver [`../reports/customer_segmentation.md`](../reports/customer_segmentation.md).

| Columna | Tipo | Descripción |
|---|---|---|
| `customer_id` | TEXT | Clave; enlaza con `dim_customer`. |
| `segment` | TEXT | VIP / Clientes frecuentes / Nuevos clientes / Clientes en riesgo / Clientes inactivos. |
| `has_purchase` | INTEGER (0/1) | 1 si el cliente tiene al menos un pedido. |
| `recency_days` | INTEGER | Días desde la última compra (proxy por adquisición si no compró). |
| `frequency` | INTEGER | Pedidos distintos. |
| `monetary` | REAL | Revenue neto de devoluciones. |
| `r_score` / `f_score` / `m_score` | INTEGER (1–5) | Puntuaciones por quintiles (5 = mejor). |
| `rfm_score` | INTEGER | `r*100 + f*10 + m`. |
| `rfm_cell` | TEXT | Concatenación `rfm` (p. ej. `543`). |
| `last_order_date` | TEXT | Fecha de la última compra (vacío si no compró). |
| `customer_segment`, `city`, `region`, `acquisition_date`, `acquisition_channel` | TEXT | Atributos heredados de `dim_customer`. |

---

## Notas para Power BI

- **Marcar `dim_date` como tabla de fechas** (`dim_date[date]`) para habilitar la
  inteligencia de tiempo (crecimiento MoM).
- Crear una relación **inactiva** `dim_date[date]` → `dim_customer[acquisition_date]`
  usada por las medidas de "New Customers" / CAC vía `USERELATIONSHIP`.
- Medidas documentadas en [`dax_measures.md`](dax_measures.md); diseño del tablero en
  [`dashboard_specification.md`](dashboard_specification.md).
