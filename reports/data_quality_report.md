# Reporte de Calidad de Datos

> Datos **simulados** (semilla `42`). Generado por `src/clean_data.py`.
> Este reporte se sobrescribe en cada ejecución.

## 1. Resumen

| Métrica | Antes de limpiar | Después de limpiar |
|---|---:|---:|
| Reglas evaluadas | 31 | 31 |
| Reglas OK | 24 | 31 |
| Reglas con error | 7 | 0 |
| Fallos críticos (bloqueantes) | 0 | 0 |
| Advertencias | 7 | 0 |

**Estado final:** ✅ Sin errores críticos. Datos aptos para análisis.

## 2. Filas originales vs procesadas

| Tabla | Filas originales | Filas procesadas | Δ |
|---|---:|---:|---:|
| `dim_date` | 547 | 547 | +0 |
| `dim_product` | 60 | 60 | +0 |
| `dim_customer` | 3,000 | 3,000 | +0 |
| `dim_channel` | 6 | 6 | +0 |
| `fact_sales` | 32,115 | 32,083 | -32 |
| `fact_marketing` | 2,188 | 2,188 | +0 |

**Registros corregidos:** 401 (duplicados eliminados: 32, nulos rellenados: 369).

## 3. Valores nulos (en origen)

| Tabla.Columna | Nulos (origen) | Severidad |
|---|---:|---|
| `dim_customer.city` | 30 | warning |
| `dim_customer.region` | 15 | warning |
| `dim_product.brand` | 2 | warning |
| `dim_product.subcategory` | 2 | warning |
| `fact_sales.discount_amount` | 160 | warning |
| `fact_sales.shipping_cost` | 160 | warning |

## 4. Duplicados

- Filas totalmente duplicadas en `fact_sales` (origen): **32**.
- Acción: eliminadas con `drop_duplicates`. Las líneas legítimas difieren en columnas
  de costo aleatorias, por lo que no se eliminan por error.

## 5. Registros inválidos (críticos)

- Detectados antes de limpiar: **0** reglas críticas con error.
- Detectados después de limpiar: **0**.
- No se encontraron claves duplicadas, FKs huérfanas, cantidades ≤ 0, montos
  negativos ni fechas fuera de periodo.

## 6. Registros corregidos

**Nulos rellenados:**

- `dim_customer.city`: 30 valores rellenados
- `dim_customer.region`: 15 valores rellenados
- `dim_product.brand`: 2 valores rellenados
- `dim_product.subcategory`: 2 valores rellenados
- `fact_sales.discount_amount`: 160 valores rellenados
- `fact_sales.shipping_cost`: 160 valores rellenados

**Texto normalizado (whitespace):**

- (ninguno)

## 7. Reconciliación de totales (fuente vs procesado)

| Métrica | Valor |
|---|---:|
| Revenue origen | 12,428,147.97 |
| Revenue procesado | 12,417,781.38 |
| Diferencia | 10,366.59 |

La diferencia se explica **en su totalidad** por la eliminación de filas duplicadas.

## 8. Reglas aplicadas (después de limpiar)

| Regla | Tabla | Severidad | Errores | Estado |
|---|---|---|---:|---|
| `duplicate_key[date_key]` | dim_date | critical | 0 | ✅ OK |
| `duplicate_key[product_id]` | dim_product | critical | 0 | ✅ OK |
| `duplicate_key[customer_id]` | dim_customer | critical | 0 | ✅ OK |
| `duplicate_key[channel_id]` | dim_channel | critical | 0 | ✅ OK |
| `nulls[order_id]` | fact_sales | critical | 0 | ✅ OK |
| `nulls[customer_id]` | fact_sales | critical | 0 | ✅ OK |
| `nulls[product_id]` | fact_sales | critical | 0 | ✅ OK |
| `nulls[order_date]` | fact_sales | critical | 0 | ✅ OK |
| `nulls[quantity]` | fact_sales | critical | 0 | ✅ OK |
| `nulls[unit_price]` | fact_sales | critical | 0 | ✅ OK |
| `nulls[city]` | dim_customer | warning | 0 | ✅ OK |
| `nulls[region]` | dim_customer | warning | 0 | ✅ OK |
| `nulls[brand]` | dim_product | warning | 0 | ✅ OK |
| `nulls[subcategory]` | dim_product | warning | 0 | ✅ OK |
| `nulls[discount_amount]` | fact_sales | warning | 0 | ✅ OK |
| `nulls[shipping_cost]` | fact_sales | warning | 0 | ✅ OK |
| `non_positive[quantity]` | fact_sales | critical | 0 | ✅ OK |
| `negative[unit_price]` | fact_sales | critical | 0 | ✅ OK |
| `negative[discount_amount]` | fact_sales | critical | 0 | ✅ OK |
| `negative[product_cost]` | fact_sales | critical | 0 | ✅ OK |
| `negative[shipping_cost]` | fact_sales | critical | 0 | ✅ OK |
| `negative[payment_fee]` | fact_sales | critical | 0 | ✅ OK |
| `negative[refund_amount]` | fact_sales | critical | 0 | ✅ OK |
| `foreign_key[customer_id->customer_id]` | fact_sales | critical | 0 | ✅ OK |
| `foreign_key[product_id->product_id]` | fact_sales | critical | 0 | ✅ OK |
| `foreign_key[channel_id->channel_id]` | fact_sales | critical | 0 | ✅ OK |
| `foreign_key[channel_id->channel_id]` | fact_marketing | critical | 0 | ✅ OK |
| `date_range[order_date]` | fact_sales | critical | 0 | ✅ OK |
| `date_range[date]` | fact_marketing | critical | 0 | ✅ OK |
| `duplicate_rows` | fact_sales | warning | 0 | ✅ OK |
| `margin_sanity` | fact_sales | warning | 0 | ✅ OK |

## 9. Reglas de limpieza aplicadas

- **Duplicados:** eliminación de filas exactas duplicadas en `fact_sales`.
- **`discount_amount` nulo → 0.0** (interpretado como "sin descuento").
- **`shipping_cost` nulo → mediana** (estimador central robusto).
- **`city` / `region` / `brand` / `subcategory` nulos → `"Unknown"`** (preserva la fila).
- **Normalización de texto:** se elimina el whitespace sobrante en columnas categóricas.

## 10. Limitaciones

- Los datos son **simulados**; el reporte demuestra el proceso, no describe un negocio real.
- El relleno de `shipping_cost` con la mediana **atenúa la varianza** de esa columna.
- No se imputan valores críticos: si existieran (FK huérfana, monto negativo), el
  pipeline se marcaría como bloqueado en lugar de inventar datos.
- La detección de duplicados en `fact_sales` es a nivel de fila completa (no hay
  clave de línea de pedido en el origen).
