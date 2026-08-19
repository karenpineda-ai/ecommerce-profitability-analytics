# Power BI

Dashboard ejecutivo del proyecto **E-commerce Profitability Analytics**.

> Los archivos `.pbix` no se incluyen en el repositorio (binarios grandes). Aquí
> se documenta el modelo, el diccionario de datos y las medidas DAX para que el
> dashboard sea reproducible.

## Conexión de datos

El dashboard se conecta a la base analítica `database/ecommerce.db` (SQLite) o a
los archivos de `data/processed/`. El modelo sigue un **esquema estrella**:

- Hechos: `FactSales`, `FactMarketing`
- Dimensiones: `DimDate`, `DimProduct`, `DimCustomer`, `DimChannel`

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
