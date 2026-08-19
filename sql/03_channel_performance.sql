-- ==========================================================================
-- 03 · CHANNEL PERFORMANCE
-- Datos SIMULADOS. Definiciones (CLAUDE.md):
--   CAC  = marketing_spend / new_customers_acquired
--   ROAS = revenue_attributed_to_channel / marketing_spend
--   net_marketing_contribution = gross_profit - marketing_spend
-- ==========================================================================

-- name: channel_performance
-- PREGUNTA DE NEGOCIO:
--   ¿Qué canales son más rentables y eficientes? ¿Cuál es su CAC, ROAS y
--   margen después de marketing?
-- COLUMNAS CALCULADAS:
--   revenue / gross_profit  : ventas atribuidas al canal (fact_sales.channel_id).
--   marketing_spend         : inversión del canal (fact_marketing).
--   new_customers           : clientes adquiridos por el canal dentro del periodo.
--   cac                     : spend / new_customers.
--   roas                    : revenue / spend.
--   net_marketing_contribution : gross_profit - spend.
--   margin_after_mkt_pct    : (gross_profit - spend) / revenue.
-- ORDEN: net_marketing_contribution DESC.
-- CONSIDERACIONES: canales sin inversión (Organic, Direct) tienen spend=0, por lo
--   que CAC y ROAS quedan NULL (NULLIF evita dividir por cero). new_customers usa
--   acquisition_date >= inicio del periodo. La atribución de revenue es de único
--   toque (el canal del pedido), simplificación documentada como limitación.
WITH line AS (
    SELECT channel_id, order_id,
           (quantity*unit_price - discount_amount + shipping_revenue) AS revenue,
           (quantity*unit_price - discount_amount + shipping_revenue)
               - product_cost - shipping_cost - payment_fee - refund_amount AS gross_profit
    FROM fact_sales
),
sales_by_ch AS (
    SELECT channel_id,
           COUNT(DISTINCT order_id) AS orders,
           SUM(revenue)             AS revenue,
           SUM(gross_profit)        AS gross_profit
    FROM line GROUP BY channel_id
),
spend_by_ch AS (
    SELECT channel_id,
           SUM(marketing_spend) AS spend,
           SUM(conversions)     AS conversions
    FROM fact_marketing GROUP BY channel_id
),
new_by_ch AS (
    SELECT ch.channel_id, COUNT(*) AS new_customers
    FROM dim_customer c
    JOIN dim_channel ch ON c.acquisition_channel = ch.channel_name
    WHERE c.acquisition_date >= (SELECT MIN(date) FROM dim_date)
    GROUP BY ch.channel_id
)
SELECT
    ch.channel_id, ch.channel_name, ch.channel_type,
    COALESCE(s.orders, 0)                                    AS orders,
    ROUND(COALESCE(s.revenue, 0), 2)                         AS revenue,
    ROUND(COALESCE(s.gross_profit, 0), 2)                    AS gross_profit,
    ROUND(100.0 * s.gross_profit / NULLIF(s.revenue, 0), 2)  AS gross_margin_pct,
    ROUND(COALESCE(m.spend, 0), 2)                           AS marketing_spend,
    COALESCE(n.new_customers, 0)                             AS new_customers,
    COALESCE(m.conversions, 0)                               AS conversions,
    ROUND(m.spend / NULLIF(n.new_customers, 0), 2)           AS cac,
    ROUND(s.revenue / NULLIF(m.spend, 0), 2)                 AS roas,
    ROUND(COALESCE(s.gross_profit, 0) - COALESCE(m.spend, 0), 2) AS net_marketing_contribution,
    ROUND(100.0 * (COALESCE(s.gross_profit, 0) - COALESCE(m.spend, 0))
          / NULLIF(s.revenue, 0), 2)                         AS margin_after_mkt_pct
FROM dim_channel ch
LEFT JOIN sales_by_ch s ON ch.channel_id = s.channel_id
LEFT JOIN spend_by_ch m ON ch.channel_id = m.channel_id
LEFT JOIN new_by_ch  n ON ch.channel_id = n.channel_id
ORDER BY net_marketing_contribution DESC;

-- name: campaign_performance
-- PREGUNTA DE NEGOCIO:
--   ¿Qué campañas son más eficientes por inversión y conversiones?
-- COLUMNAS: spend, impressions, clicks, conversions, ctr_pct (clicks/impresiones),
--   cvr_pct (conversiones/clicks), cost_per_conversion.
-- ORDEN: spend DESC.
-- CONSIDERACIONES: métricas de embudo simuladas; no hay revenue directo por campaña
--   (la atribución de ventas es a nivel de canal, no de campaña).
SELECT
    ch.channel_name,
    m.campaign_name,
    ROUND(SUM(m.marketing_spend), 2)                              AS spend,
    SUM(m.impressions)                                            AS impressions,
    SUM(m.clicks)                                                 AS clicks,
    SUM(m.conversions)                                            AS conversions,
    ROUND(100.0 * SUM(m.clicks) / NULLIF(SUM(m.impressions), 0), 2) AS ctr_pct,
    ROUND(100.0 * SUM(m.conversions) / NULLIF(SUM(m.clicks), 0), 2) AS cvr_pct,
    ROUND(SUM(m.marketing_spend) / NULLIF(SUM(m.conversions), 0), 2) AS cost_per_conversion
FROM fact_marketing m
JOIN dim_channel ch ON m.channel_id = ch.channel_id
GROUP BY ch.channel_name, m.campaign_name
ORDER BY spend DESC;
