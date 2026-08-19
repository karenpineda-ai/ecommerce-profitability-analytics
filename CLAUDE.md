# Proyecto: E-commerce Profitability Analytics

## Propósito

Construir un proyecto profesional de portafolio que demuestre habilidades de Business Analysis, Data Analytics, SQL, Python, Power BI y marketing analytics.

El proyecto analizará la rentabilidad de un e-commerce utilizando datos simulados realistas. El objetivo es convertir datos comerciales en recomendaciones accionables sobre productos, categorías, clientes y canales de marketing.

## Perfil profesional

La autora es una Business Analyst y Data Analyst con experiencia en:

- Business Intelligence.
- Power BI.
- SQL.
- Python.
- Excel.
- Marketing digital.
- E-commerce.
- Análisis comercial.
- Modelamiento de indicadores.
- Comunicación ejecutiva.

El proyecto debe reflejar una combinación equilibrada entre capacidad técnica y pensamiento de negocio.

## Objetivo de negocio

Responder las siguientes preguntas:

1. ¿Qué productos y categorías generan mayor rentabilidad?
2. ¿Qué productos tienen muchas ventas, pero bajo margen?
3. ¿Qué canales de marketing son más eficientes?
4. ¿Qué segmentos de clientes generan más valor?
5. ¿Dónde existen oportunidades para mejorar el margen?
6. ¿Qué decisiones debería tomar un gerente de e-commerce?

## Alcance técnico

El proyecto debe incluir:

- Dataset simulado reproducible.
- Limpieza y validación de datos con Python.
- Base de datos analítica en SQLite o PostgreSQL.
- Consultas SQL documentadas.
- Análisis exploratorio con Python.
- Modelo dimensional tipo estrella.
- Medidas DAX documentadas para Power BI.
- Dashboard ejecutivo.
- Informe de hallazgos.
- Presentación profesional para LinkedIn.
- README completo.
- Pruebas de calidad de datos.
- Registro de supuestos y limitaciones.

## Restricciones importantes

- No utilizar datos personales reales.
- No utilizar información confidencial.
- No presentar datos simulados como datos reales.
- No inventar fuentes externas.
- No crear resultados sin que exista una lógica reproducible.
- No utilizar credenciales, API keys ni contraseñas en el repositorio.
- No incluir archivos `.env` en Git.
- Utilizar datos simulados y declararlo claramente.
- Mantener separación entre código, datos, documentación y resultados.
- No sobrescribir archivos importantes sin confirmación.
- Antes de eliminar o modificar archivos existentes, explicar el cambio.
- No instalar dependencias sin informarlo previamente.
- Ejecutar pruebas después de cada etapa importante.

## Tecnologías

Usar preferentemente:

- Python 3.11 o superior.
- pandas.
- numpy.
- matplotlib.
- seaborn.
- scikit-learn solamente si se necesita.
- SQLite como base de datos inicial.
- SQL estándar compatible con SQLite.
- Power BI para el dashboard.
- DAX para las medidas.
- Git y GitHub para control de versiones.
- Markdown para la documentación.

## Estructura de carpetas esperada

```text
ecommerce-profitability-analytics/
│
├── CLAUDE.md
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
│
├── database/
│   ├── schema.sql
│   ├── seed.sql
│   └── ecommerce.db
│
├── notebooks/
│   ├── 01_data_generation.ipynb
│   ├── 02_data_quality.ipynb
│   ├── 03_exploratory_analysis.ipynb
│   └── 04_customer_segmentation.ipynb
│
├── src/
│   ├── config.py
│   ├── generate_data.py
│   ├── clean_data.py
│   ├── validate_data.py
│   ├── load_database.py
│   ├── analysis.py
│   └── utils.py
│
├── sql/
│   ├── 01_revenue_analysis.sql
│   ├── 02_profitability_analysis.sql
│   ├── 03_channel_performance.sql
│   ├── 04_customer_rfm.sql
│   └── 05_data_quality.sql
│
├── powerbi/
│   ├── README.md
│   ├── data_dictionary.md
│   └── dax_measures.md
│
├── reports/
│   ├── executive_summary.md
│   ├── findings.md
│   ├── assumptions.md
│   └── limitations.md
│
├── presentation/
│   └── linkedin_case_study.md
│
└── tests/
    ├── test_data_quality.py
    └── test_calculations.py
```

## Modelo de datos

Crear las siguientes entidades:

### DimDate

- date_key
- date
- year
- quarter
- month
- month_name
- week
- day_of_week

### DimProduct

- product_id
- product_name
- category
- subcategory
- brand
- unit_cost
- list_price
- supplier
- active_flag

### DimCustomer

- customer_id
- customer_segment
- city
- region
- acquisition_date
- acquisition_channel

### DimChannel

- channel_id
- channel_name
- channel_type

### FactSales

- order_id
- order_date
- customer_id
- product_id
- channel_id
- quantity
- unit_price
- discount_amount
- shipping_revenue
- product_cost
- shipping_cost
- payment_fee
- returned_flag
- refund_amount

### FactMarketing

- date
- channel_id
- campaign_name
- impressions
- clicks
- leads
- conversions
- marketing_spend

## Reglas para los datos simulados

Generar datos para al menos 18 meses.

La base debe contener:

- Entre 2.000 y 5.000 clientes.
- Entre 40 y 80 productos.
- Entre 10.000 y 30.000 pedidos.
- Entre 6 y 10 categorías.
- Entre 5 y 7 canales de adquisición.
- Variación estacional.
- Diferencias realistas de margen entre categorías.
- Productos con alta venta y bajo margen.
- Productos con baja venta y alto margen.
- Clientes nuevos y recurrentes.
- Devoluciones.
- Descuentos.
- Costos logísticos.
- Inversión de marketing por canal.
- Valores nulos o inconsistentes controlados para probar validaciones.

Las relaciones entre tablas deben ser lógicas y reproducibles mediante una semilla aleatoria fija.

## Definiciones de negocio

Revenue:

```text
quantity × unit_price - discount_amount + shipping_revenue
```

Product Cost:

```text
quantity × unit_cost
```

Gross Profit:

```text
Revenue - Product Cost - Shipping Cost - Payment Fee - Refund Amount
```

Gross Margin %:

```text
Gross Profit / Revenue
```

Average Order Value:

```text
Revenue / Number of Orders
```

CAC:

```text
Marketing Spend / New Customers Acquired
```

ROAS:

```text
Revenue Attributed to Channel / Marketing Spend
```

Net Marketing Contribution:

```text
Gross Profit - Marketing Spend
```

Return Rate:

```text
Returned Orders / Total Orders
```

## Indicadores principales

Construir y documentar al menos:

- Total Revenue.
- Gross Profit.
- Gross Margin %.
- Number of Orders.
- Units Sold.
- Average Order Value.
- Average Discount.
- Return Rate.
- Marketing Spend.
- CAC.
- ROAS.
- Net Marketing Contribution.
- Revenue per Customer.
- Repeat Purchase Rate.
- Customer Lifetime Value aproximado.
- Revenue growth month over month.
- Gross profit growth month over month.

## Análisis requeridos

Desarrollar análisis sobre:

1. Revenue y profit por mes.
2. Revenue y profit por categoría.
3. Margen por producto.
4. Productos con alta venta y bajo margen.
5. Productos con bajo volumen y alto margen.
6. Rentabilidad por canal.
7. CAC y ROAS por canal.
8. Rendimiento por campaña.
9. Segmentación RFM.
10. Clientes en riesgo.
11. Devoluciones por categoría.
12. Costos de envío por zona.
13. Descuentos y su relación con margen.
14. Estacionalidad.
15. Top 10 productos por contribución al margen.

## Reglas de calidad

Implementar validaciones para:

- Claves duplicadas.
- Valores nulos.
- Fechas fuera del periodo.
- Cantidades iguales o menores que cero.
- Precios negativos.
- Costos negativos.
- Margen fuera de rangos razonables.
- Pedidos sin cliente.
- Pedidos sin producto.
- Productos inexistentes.
- Diferencias entre totales fuente y totales procesados.

Cada validación debe:

- Tener una función independiente.
- Devolver un resultado claro.
- Registrar el número de errores.
- Explicar si el error bloquea o no el proceso.
- Contar con al menos una prueba automatizada.

## Estándar de código

- Escribir código modular.
- Utilizar nombres en inglés para tablas, columnas y funciones.
- Utilizar comentarios únicamente cuando agreguen contexto.
- Evitar valores hardcodeados innecesarios.
- Usar configuración centralizada.
- Mantener funciones pequeñas.
- Documentar parámetros y resultados.
- Manejar errores de forma explícita.
- No ocultar errores con excepciones genéricas.
- Utilizar type hints cuando sea razonable.
- Formatear el código de manera consistente.

## Dashboard Power BI

Diseñar un dashboard con las siguientes páginas:

### Página 1: Executive Overview

- Revenue.
- Gross Profit.
- Gross Margin %.
- Orders.
- Average Order Value.
- Marketing Spend.
- ROAS.
- Tendencia mensual.
- Filtros por fecha, categoría y canal.

### Página 2: Product Profitability

- Revenue por categoría.
- Gross profit por categoría.
- Margen por producto.
- Tabla de productos.
- Matriz de volumen versus margen.

### Página 3: Marketing Performance

- Spend.
- Revenue.
- CAC.
- ROAS.
- Conversions.
- Margen después de marketing.
- Comparación entre canales.

### Página 4: Customer Analytics

- RFM.
- Clientes VIP.
- Clientes en riesgo.
- Repeat Purchase Rate.
- Revenue por segmento.
- Customer Lifetime Value aproximado.

### Página 5: Operational Insights

- Devoluciones.
- Costos de envío.
- Descuentos.
- Productos con alertas.
- Oportunidades priorizadas.

## Medidas DAX

Crear un archivo `powerbi/dax_measures.md` con las medidas necesarias.

Cada medida debe contener:

- Nombre.
- Fórmula.
- Descripción.
- Contexto de uso.
- Consideraciones o limitaciones.

## Documentación del proyecto

El README debe incluir:

- Descripción ejecutiva.
- Problema de negocio.
- Objetivos.
- Arquitectura.
- Estructura de carpetas.
- Instalación.
- Ejecución.
- Generación de datos.
- Validación.
- Carga de base de datos.
- Ejecución de consultas.
- Conexión con Power BI.
- Indicadores.
- Hallazgos.
- Supuestos.
- Limitaciones.
- Mejoras futuras.
- Cómo contactar a la autora.

## Forma de trabajo

Trabaja por fases y no intentes crear todo de una sola vez.

Fase 0: inspeccionar el entorno y verificar Python, Git y dependencias.

Fase 1: crear la estructura del proyecto y archivos base.

Fase 2: crear el generador de datos simulados.

Fase 3: crear limpieza y validación.

Fase 4: crear la base SQLite y las tablas.

Fase 5: crear consultas SQL.

Fase 6: crear análisis exploratorio.

Fase 7: crear segmentación RFM.

Fase 8: crear documentación y medidas DAX.

Fase 9: crear pruebas.

Fase 10: revisar el proyecto completo.

Al terminar cada fase:

1. Explica qué archivos creaste o modificaste.
2. Ejecuta las pruebas correspondientes.
3. Resume los resultados.
4. Indica cualquier supuesto.
5. Espera mi aprobación antes de avanzar a la siguiente fase.

No avances automáticamente a la siguiente fase sin mi aprobación.

## Criterios de aceptación

El proyecto estará terminado únicamente cuando:

- El código se ejecute desde cero.
- Los datos se generen con una semilla reproducible.
- Las validaciones funcionen.
- La base de datos pueda recrearse.
- Las consultas SQL produzcan resultados.
- Los indicadores sean matemáticamente coherentes.
- El análisis incluya recomendaciones.
- El README permita reproducir el proyecto.
- Las pruebas pasen.
- Los datos estén claramente identificados como simulados.
- El proyecto pueda presentarse en una entrevista técnica.