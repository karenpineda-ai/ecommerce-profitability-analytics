# Segmentación de Clientes (RFM)

> **Datos simulados** (semilla 42). Metodología reproducible; todas las cifras se
> calculan desde `data/processed/`. Resultado: `data/processed/customer_rfm.csv`.

## 1. Metodología

- **Fecha de análisis:** 2025-06-30 (último pedido en los datos).
- **Recency** = días desde la última compra. **Frequency** = pedidos distintos.
  **Monetary** = revenue neto de devoluciones.
- **Puntuación 1–5 por quintiles basados en rango** (grupos de igual tamaño): evita
  errores por empates y garantiza puntuaciones no nulas. R: menos días → 5.
  F y M: mayor valor → 5.
- **Base RFM:** 2,443 clientes con al menos un pedido, de 3,000
  totales. Los 557 clientes sin compras se incluyen como
  "Clientes inactivos" (scores mínimos), de modo que **cada cliente tiene un segmento**.

## 2. Umbrales por puntuación (clientes con compra)

Rangos del valor subyacente en cada banda de score:

**Recency (días)** — score 5 = compra más reciente
| r_score | min | max |
|---|---:|---:|
| 1 | 153.00 | 542.00 |
| 2 | 77.00 | 153.00 |
| 3 | 40.00 | 77.00 |
| 4 | 16.00 | 40.00 |
| 5 | 0.00 | 16.00 |

**Frequency (pedidos)** — score 5 = mayor frecuencia
| f_score | min | max |
|---|---:|---:|
| 1 | 1.00 | 2.00 |
| 2 | 2.00 | 4.00 |
| 3 | 4.00 | 7.00 |
| 4 | 7.00 | 12.00 |
| 5 | 13.00 | 85.00 |

**Monetary** — score 5 = mayor valor
| m_score | min | max |
|---|---:|---:|
| 1 | 0.00 | 626.57 |
| 2 | 628.04 | 1,711.30 |
| 3 | 1,712.91 | 3,611.01 |
| 4 | 3,623.58 | 7,331.70 |
| 5 | 7,335.86 | 53,545.42 |

## 3. Definición de segmentos (escalera de decisión, primer match gana)

1. **VIP:** `M≥4 y F≥4 y R≥3` (alto valor y aún activos).
2. **Clientes en riesgo:** `R≤2 y (F≥3 o M≥4)` (fueron valiosos, dejaron de comprar).
3. **Clientes inactivos:** `R≤2` restantes (baja recencia y bajo valor) + clientes sin compras.
4. **Nuevos clientes:** `F≤2 y R≥3` (pocas compras, recientes).
5. **Clientes frecuentes:** resto (`R≥3 y F≥3`, compradores recurrentes no-VIP).

La escalera es **mutuamente excluyente y cubre el 100%** de las combinaciones R×F×M.

## 4. Distribución de segmentos

| Segmento | Clientes | % clientes | Recency prom. | Freq. prom. | Monetary total | % valor |
|---|---:|---:|---:|---:|---:|---:|
| VIP | 619 | 20.6% | 29 | 19.2 | 6,996,479 | 62.3% |
| Clientes frecuentes | 387 | 12.9% | 30 | 6.2 | 1,087,181 | 9.7% |
| Nuevos clientes | 460 | 15.3% | 33 | 1.9 | 516,312 | 4.6% |
| Clientes en riesgo | 487 | 16.2% | 150 | 8.0 | 2,200,527 | 19.6% |
| Clientes inactivos | 1,047 | 34.9% | 176 | 0.9 | 429,781 | 3.8% |

## 5. Recomendaciones por segmento

### VIP
Programa de fidelización premium, acceso anticipado y atención preferente. Proteger la relación: son la principal fuente de valor.

### Clientes frecuentes
Incentivar mayor ticket y cross-sell; upgrade hacia VIP con beneficios por volumen. Mantener la cadencia de compra.

### Nuevos clientes
Onboarding y segunda compra: emails de bienvenida, descuento de reactivación acotado y recomendación de productos afines.

### Clientes en riesgo
Campaña de recuperación priorizada por monetary: recordatorio, oferta personalizada y encuesta de motivos de abandono.

### Clientes inactivos
Reactivación de bajo costo (email masivo) o depuración de la base. Evitar inversión alta: baja probabilidad de retorno.

## 6. Uso en Power BI

`customer_rfm.csv` tiene **una fila por cliente** con columnas planas listas para
modelar: `customer_id` (clave), `segment`, `r_score`/`f_score`/`m_score`,
`rfm_score`, `recency_days`, `frequency`, `monetary`, `has_purchase` y atributos
de cliente. Se relaciona con `dim_customer[customer_id]` (1:1) para filtrar todo
el modelo por segmento.

## 7. Limitaciones del método

- **RFM es descriptivo/histórico:** no predice comportamiento futuro ni CLV probabilístico.
- **Quintiles por rango:** los empates (p. ej. muchos clientes con 1 pedido) se
  reparten por orden estable; los cortes son relativos a esta base, no absolutos.
- **Umbrales de segmento** (≥3, ≥4, ≤2) son una convención de negocio, no óptimos
  estadísticos; ajustables según estrategia.
- **Clientes sin compras** se marcan inactivos con recency basada en la fecha de
  adquisición (proxy), no en una compra real.
- Datos **simulados**: la distribución refleja el generador, no un negocio real.
