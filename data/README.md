# Data

> ⚠️ **Todos los datos de este proyecto son SIMULADOS.**
> Se generan sintéticamente mediante código con una **semilla aleatoria fija**,
> por lo que son 100 % reproducibles. **No** provienen de ninguna empresa real y
> **no** contienen información personal, confidencial ni sensible.

## Estructura

| Carpeta | Contenido | Versionado en Git |
|---|---|---|
| `raw/` | Datos crudos generados por `src/generate_data.py` (con nulos e inconsistencias controladas para probar validaciones). | ❌ No (regenerable) |
| `processed/` | Datos limpios y validados por `src/clean_data.py` y `src/validate_data.py`. | ❌ No (regenerable) |

Ambas carpetas se excluyen del repositorio mediante `.gitignore` porque los
archivos son **regenerables** a partir del código. Se conservan en Git solo con
un marcador `.gitkeep`.

## Cómo regenerar los datos

```bash
python -m src.generate_data     # crea los archivos en data/raw/
python -m src.clean_data        # produce data/processed/
```

> Disponible a partir de la **Fase 2**. La semilla se define en `src/config.py`.

## Declaración

Estos datos se presentan **explícitamente como simulados** y no deben
interpretarse como métricas reales de negocio.

## Resumen del dataset generado

<!-- SUMMARY:START -->
**Datos simulados** (semilla `42`). Periodo: 18 meses desde 2024-01-01.

| Tabla | Filas | Columnas |
|---|---:|---:|
| `dim_date` | 547 | 8 |
| `dim_product` | 60 | 9 |
| `dim_customer` | 3,000 | 6 |
| `dim_channel` | 6 | 3 |
| `fact_sales` | 32,115 | 14 |
| `fact_marketing` | 2,188 | 8 |

**Problemas de calidad inyectados (controlados):**

- `customer_city_null`: 30
- `customer_region_null`: 15
- `product_brand_null`: 2
- `product_subcategory_null`: 2
- `sales_discount_null`: 160
- `sales_shipping_cost_null`: 160
- `sales_duplicate_rows`: 32
<!-- SUMMARY:END -->
