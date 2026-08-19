# Power BI

Dashboard ejecutivo del proyecto **E-commerce Profitability Analytics**.

> Los archivos `.pbix` no se incluyen en el repositorio (binarios grandes). Aquí
> se documenta el modelo, el diccionario de datos y las medidas DAX para que el
> dashboard sea reproducible.

## Conexión de datos

El dashboard se conecta a la base analítica `database/ecommerce.db` (SQLite) o a
los archivos de `data/processed/`. El modelo sigue un **esquema estrella**:

- Hechos: `fact_sales`, `fact_marketing`
- Dimensiones: `dim_date`, `dim_product`, `dim_customer`, `dim_channel`

> **Nomenclatura:** `CLAUDE.md` nombra las entidades del modelo lógico en PascalCase
> (`FactSales`, `DimDate`, …). Las tablas **físicas** implementadas (SQLite, CSVs y
> medidas DAX) usan snake_case (`fact_sales`, `dim_date`, …). Ambos nombres se refieren
> a la misma tabla; toda la implementación y esta documentación usan snake_case.

## Checklist de configuración del modelo (antes de construir el dashboard)

Pasos manuales en Power BI de los que dependen varias medidas; verificar en orden:

- [ ] **Cargar** las 6 tablas + `customer_rfm` desde `data/processed/` (o vía ODBC a `ecommerce.db`).
- [ ] **Marcar `dim_date` como tabla de fechas** (Modelado → Marcar como tabla de fechas → `dim_date[date]`). *Requerido por* `Revenue Growth %` y `Gross Profit Growth %`.
- [ ] **Relaciones activas** `dim_date[date] → fact_sales[order_date]` y `dim_date[date] → fact_marketing[date]`; más producto/cliente/canal (ver [`data_dictionary.md`](data_dictionary.md)).
- [ ] **Relación inactiva** `dim_date[date] → dim_customer[acquisition_date]`. *Requerida por* `New Customers` y `CAC` (vía `USERELATIONSHIP`).
- [ ] **Relación 1:1** `customer_rfm[customer_id] → dim_customer[customer_id]` para filtrar por segmento RFM.
- [ ] **Tabla `_Measures`** (vacía) donde alojar todas las medidas de [`dax_measures.md`](dax_measures.md).
- [ ] **Verificar:** `New Customers` sin `USERELATIONSHIP` cuenta por fecha de pedido (incorrecto); `Revenue Growth %` da BLANK en el primer mes (esperado).

## Páginas del dashboard

1. **Executive Overview** — Revenue, Gross Profit, Margin %, Orders, AOV, Spend, ROAS y tendencia mensual.
2. **Product Profitability** — Revenue/Profit por categoría, margen por producto, matriz volumen vs. margen.
3. **Marketing Performance** — Spend, Revenue, CAC, ROAS, conversiones, margen post-marketing.
4. **Customer Analytics** — RFM, VIP, clientes en riesgo, repeat rate, CLV aproximado.
5. **Operational Insights** — Devoluciones, costos de envío, descuentos, alertas y oportunidades.

## Documentación relacionada

- [`data_dictionary.md`](data_dictionary.md) — diccionario de datos y modelo.
- [`dax_measures.md`](dax_measures.md) — medidas DAX documentadas.
- [`dashboard_specification.md`](dashboard_specification.md) — páginas, visuales,
  filtros, colores y **guía de conexión** (CSV u ODBC/SQLite).

> El archivo `.pbix` **no** está incluido: este directorio contiene la
> especificación reproducible para construirlo, no un tablero ya finalizado.
