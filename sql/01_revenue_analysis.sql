-- ==========================================================================
-- 01 · REVENUE ANALYSIS
-- Datos SIMULADOS. Métricas según CLAUDE.md:
--   revenue      = quantity*unit_price - discount_amount + shipping_revenue
--   gross_profit = revenue - product_cost - shipping_cost - payment_fee - refund_amount
-- Cada bloque comienza con "-- name: <slug>" para su ejecución individual.
-- ==========================================================================

-- name: monthly_revenue
-- PREGUNTA DE NEGOCIO:
--   ¿Cómo evolucionan revenue, gross profit y margen mes a mes? ¿Hay estacionalidad?
-- COLUMNAS CALCULADAS:
--   revenue / gross_profit : sumas mensuales (fórmulas de CLAUDE.md).
--   gross_margin_pct       : gross_profit / revenue * 100.
--   avg_order_value        : revenue / nº de pedidos distintos.
--   *_mom_pct              : crecimiento % mes contra mes (LAG window).
-- ORDEN: cronológico (year_month ascendente).
-- CONSIDERACIONES: revenue y gross_profit ya descuentan devoluciones vía
--   refund_amount; NULLIF evita división por cero en meses sin ventas.
WITH line AS (
    SELECT
        substr(order_date, 1, 7) AS year_month,
        order_id,
        (quantity * unit_price - discount_amount + shipping_revenue) AS revenue,
        (quantity * unit_price - discount_amount + shipping_revenue)
            - product_cost - shipping_cost - payment_fee - refund_amount AS gross_profit
    FROM fact_sales
),
monthly AS (
    SELECT
        year_month,
        COUNT(DISTINCT order_id) AS orders,
        SUM(revenue)             AS revenue,
        SUM(gross_profit)        AS gross_profit
    FROM line
    GROUP BY year_month
)
SELECT
    year_month,
    orders,
    ROUND(revenue, 2)                                              AS revenue,
    ROUND(gross_profit, 2)                                         AS gross_profit,
    ROUND(100.0 * gross_profit / NULLIF(revenue, 0), 2)            AS gross_margin_pct,
    ROUND(revenue / NULLIF(orders, 0), 2)                          AS avg_order_value,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year_month))
          / NULLIF(LAG(revenue) OVER (ORDER BY year_month), 0), 2) AS revenue_mom_pct,
    ROUND(100.0 * (gross_profit - LAG(gross_profit) OVER (ORDER BY year_month))
          / NULLIF(LAG(gross_profit) OVER (ORDER BY year_month), 0), 2) AS gross_profit_mom_pct
FROM monthly
ORDER BY year_month;
