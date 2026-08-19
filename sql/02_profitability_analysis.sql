-- ==========================================================================
-- 02 · PROFITABILITY ANALYSIS
-- Datos SIMULADOS. revenue / gross_profit según CLAUDE.md (ver 01).
-- ==========================================================================

-- name: margin_by_category
-- PREGUNTA DE NEGOCIO:
--   ¿Qué categorías generan más revenue y profit, y cuál es su margen?
-- COLUMNAS: units (unidades), revenue, gross_profit, gross_margin_pct,
--   profit_per_unit (gross_profit / units).
-- ORDEN: gross_profit descendente (mayor contribución primero).
-- CONSIDERACIONES: gross_profit ya netea devoluciones (refund_amount).
WITH line AS (
    SELECT p.category,
           f.order_id, f.quantity,
           (f.quantity*f.unit_price - f.discount_amount + f.shipping_revenue) AS revenue,
           (f.quantity*f.unit_price - f.discount_amount + f.shipping_revenue)
               - f.product_cost - f.shipping_cost - f.payment_fee - f.refund_amount AS gross_profit
    FROM fact_sales f
    JOIN dim_product p ON f.product_id = p.product_id
)
SELECT
    category,
    COUNT(DISTINCT order_id)                            AS orders,
    SUM(quantity)                                       AS units,
    ROUND(SUM(revenue), 2)                              AS revenue,
    ROUND(SUM(gross_profit), 2)                         AS gross_profit,
    ROUND(100.0 * SUM(gross_profit) / NULLIF(SUM(revenue), 0), 2) AS gross_margin_pct,
    ROUND(SUM(gross_profit) / NULLIF(SUM(quantity), 0), 2)        AS profit_per_unit
FROM line
GROUP BY category
ORDER BY gross_profit DESC;

-- name: high_volume_low_margin
-- PREGUNTA DE NEGOCIO:
--   ¿Qué productos venden mucho pero rinden poco margen? (candidatos a revisar precio/costo)
-- COLUMNAS: units, revenue, gross_profit, gross_margin_pct.
-- ORDEN: units DESC, gross_margin_pct ASC.
-- CONSIDERACIONES: "alto" y "bajo" se definen respecto al PROMEDIO de productos
--   (units >= avg units y margen <= avg margen). Umbral documentado; con más
--   datos podría usarse la mediana.
WITH prod AS (
    SELECT f.product_id, p.product_name, p.category,
           SUM(f.quantity) AS units,
           SUM(f.quantity*f.unit_price - f.discount_amount + f.shipping_revenue) AS revenue,
           SUM((f.quantity*f.unit_price - f.discount_amount + f.shipping_revenue)
               - f.product_cost - f.shipping_cost - f.payment_fee - f.refund_amount) AS gross_profit
    FROM fact_sales f
    JOIN dim_product p ON f.product_id = p.product_id
    GROUP BY f.product_id, p.product_name, p.category
),
scored AS (
    SELECT *, 100.0 * gross_profit / NULLIF(revenue, 0) AS gross_margin_pct FROM prod
),
stats AS (SELECT AVG(units) AS avg_units, AVG(gross_margin_pct) AS avg_margin FROM scored)
SELECT s.product_id, s.product_name, s.category,
       s.units, ROUND(s.revenue, 2) AS revenue,
       ROUND(s.gross_profit, 2) AS gross_profit,
       ROUND(s.gross_margin_pct, 2) AS gross_margin_pct
FROM scored s, stats
WHERE s.units >= stats.avg_units AND s.gross_margin_pct <= stats.avg_margin
ORDER BY s.units DESC, s.gross_margin_pct ASC;

-- name: low_volume_high_margin
-- PREGUNTA DE NEGOCIO:
--   ¿Qué productos rinden alto margen pero venden poco? (candidatos a impulsar).
-- COLUMNAS: iguales al bloque anterior.
-- ORDEN: gross_margin_pct DESC, units ASC.
-- CONSIDERACIONES: umbral por promedio (units <= avg, margen >= avg).
WITH prod AS (
    SELECT f.product_id, p.product_name, p.category,
           SUM(f.quantity) AS units,
           SUM(f.quantity*f.unit_price - f.discount_amount + f.shipping_revenue) AS revenue,
           SUM((f.quantity*f.unit_price - f.discount_amount + f.shipping_revenue)
               - f.product_cost - f.shipping_cost - f.payment_fee - f.refund_amount) AS gross_profit
    FROM fact_sales f
    JOIN dim_product p ON f.product_id = p.product_id
    GROUP BY f.product_id, p.product_name, p.category
),
scored AS (
    SELECT *, 100.0 * gross_profit / NULLIF(revenue, 0) AS gross_margin_pct FROM prod
),
stats AS (SELECT AVG(units) AS avg_units, AVG(gross_margin_pct) AS avg_margin FROM scored)
SELECT s.product_id, s.product_name, s.category,
       s.units, ROUND(s.revenue, 2) AS revenue,
       ROUND(s.gross_profit, 2) AS gross_profit,
       ROUND(s.gross_margin_pct, 2) AS gross_margin_pct
FROM scored s, stats
WHERE s.units <= stats.avg_units AND s.gross_margin_pct >= stats.avg_margin
ORDER BY s.gross_margin_pct DESC, s.units ASC;

-- name: top10_margin_contribution
-- PREGUNTA DE NEGOCIO:
--   ¿Cuáles son los 10 productos que más contribuyen al gross profit total?
-- COLUMNAS: gross_profit y pct_of_total_profit (participación % sobre el total).
-- ORDEN: gross_profit DESC, TOP 10.
-- CONSIDERACIONES: la participación usa el gross_profit total de todos los productos.
WITH prod AS (
    SELECT f.product_id, p.product_name, p.category,
           SUM((f.quantity*f.unit_price - f.discount_amount + f.shipping_revenue)
               - f.product_cost - f.shipping_cost - f.payment_fee - f.refund_amount) AS gross_profit
    FROM fact_sales f
    JOIN dim_product p ON f.product_id = p.product_id
    GROUP BY f.product_id, p.product_name, p.category
)
SELECT product_id, product_name, category,
       ROUND(gross_profit, 2) AS gross_profit,
       ROUND(100.0 * gross_profit / SUM(gross_profit) OVER (), 2) AS pct_of_total_profit
FROM prod
ORDER BY gross_profit DESC
LIMIT 10;

-- name: returns_by_category
-- PREGUNTA DE NEGOCIO:
--   ¿Dónde se concentran las devoluciones y cuánto revenue reembolsan?
-- COLUMNAS: returned_lines, return_rate_line_pct, total_refund,
--   refund_pct_of_revenue.
-- ORDEN: return_rate_line_pct DESC.
-- CONSIDERACIONES: la tasa se calcula a nivel de LÍNEA de pedido (no de orden);
--   refund_amount es el monto efectivamente reembolsado.
WITH line AS (
    SELECT p.category, f.returned_flag, f.refund_amount,
           (f.quantity*f.unit_price - f.discount_amount + f.shipping_revenue) AS revenue
    FROM fact_sales f
    JOIN dim_product p ON f.product_id = p.product_id
)
SELECT
    category,
    COUNT(*)                                              AS lines,
    SUM(returned_flag)                                    AS returned_lines,
    ROUND(100.0 * SUM(returned_flag) / COUNT(*), 2)       AS return_rate_line_pct,
    ROUND(SUM(refund_amount), 2)                          AS total_refund,
    ROUND(100.0 * SUM(refund_amount) / NULLIF(SUM(revenue), 0), 2) AS refund_pct_of_revenue
FROM line
GROUP BY category
ORDER BY return_rate_line_pct DESC;
