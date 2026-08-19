-- ==========================================================================
-- 04 · CUSTOMER RFM
-- Datos SIMULADOS. RFM = Recency, Frequency, Monetary.
--   analysis_date = fecha máxima de pedido en los datos.
--   recency_days  = analysis_date - última compra del cliente.
--   frequency     = nº de pedidos distintos.
--   monetary      = revenue neto de devoluciones (revenue - refund_amount).
-- Scores 1..5 con NTILE (5 = mejor). Solo clientes con al menos un pedido.
-- ==========================================================================

-- name: rfm_scores
-- PREGUNTA DE NEGOCIO:
--   ¿Cómo se distribuyen los clientes según Recency, Frequency y Monetary?
-- COLUMNAS: recency_days, frequency, monetary, r_score/f_score/m_score (1..5),
--   rfm_cell (concatenación) y rfm_segment (clasificación de negocio).
-- ORDEN: m_score DESC, f_score DESC, r_score DESC.
-- CONSIDERACIONES: clientes sin pedidos no aparecen (no hay RFM). monetary neto
--   de refund_amount para reflejar valor realmente retenido.
WITH line AS (
    SELECT customer_id, order_id, order_date,
           (quantity*unit_price - discount_amount + shipping_revenue) AS revenue,
           refund_amount
    FROM fact_sales
),
agg AS (
    SELECT customer_id,
           MAX(order_date)          AS last_order_date,
           COUNT(DISTINCT order_id) AS frequency,
           SUM(revenue - refund_amount) AS monetary
    FROM line GROUP BY customer_id
),
ref AS (SELECT MAX(order_date) AS analysis_date FROM fact_sales),
rfm AS (
    SELECT a.customer_id, a.last_order_date, a.frequency,
           ROUND(a.monetary, 2) AS monetary,
           CAST(julianday(r.analysis_date) - julianday(a.last_order_date) AS INTEGER) AS recency_days,
           NTILE(5) OVER (ORDER BY julianday(a.last_order_date) ASC) AS r_score,
           NTILE(5) OVER (ORDER BY a.frequency ASC)                  AS f_score,
           NTILE(5) OVER (ORDER BY a.monetary ASC)                   AS m_score
    FROM agg a CROSS JOIN ref r
)
SELECT
    c.customer_id, c.customer_segment, c.region,
    rfm.recency_days, rfm.frequency, rfm.monetary,
    rfm.r_score, rfm.f_score, rfm.m_score,
    (rfm.r_score || rfm.f_score || rfm.m_score) AS rfm_cell,
    -- Canonical segment ladder (matches src/customer_segmentation.py, first match wins).
    -- Base = purchasers only; non-buyers are added as 'Clientes inactivos' by the
    -- Python segmentation that feeds Power BI.
    CASE
        WHEN rfm.m_score >= 4 AND rfm.f_score >= 4 AND rfm.r_score >= 3 THEN 'VIP'
        WHEN rfm.r_score <= 2 AND (rfm.f_score >= 3 OR rfm.m_score >= 4) THEN 'Clientes en riesgo'
        WHEN rfm.r_score <= 2                                           THEN 'Clientes inactivos'
        WHEN rfm.f_score <= 2 AND rfm.r_score >= 3                      THEN 'Nuevos clientes'
        ELSE 'Clientes frecuentes'
    END AS rfm_segment
FROM rfm
JOIN dim_customer c ON rfm.customer_id = c.customer_id
ORDER BY rfm.m_score DESC, rfm.f_score DESC, rfm.r_score DESC;

-- name: rfm_segment_summary
-- PREGUNTA DE NEGOCIO:
--   ¿Cuántos clientes y cuánto valor aporta cada segmento RFM?
-- COLUMNAS: customers, avg_recency_days, avg_frequency, total_monetary,
--   avg_monetary, pct_of_customers.
-- ORDEN: total_monetary DESC.
-- CONSIDERACIONES: base = clientes con pedidos (mismos supuestos que rfm_scores).
WITH line AS (
    SELECT customer_id, order_id, order_date,
           (quantity*unit_price - discount_amount + shipping_revenue) AS revenue, refund_amount
    FROM fact_sales
),
agg AS (
    SELECT customer_id, MAX(order_date) AS last_order_date,
           COUNT(DISTINCT order_id) AS frequency, SUM(revenue - refund_amount) AS monetary
    FROM line GROUP BY customer_id
),
ref AS (SELECT MAX(order_date) AS analysis_date FROM fact_sales),
rfm AS (
    SELECT a.customer_id, a.frequency, a.monetary,
           CAST(julianday(r.analysis_date) - julianday(a.last_order_date) AS INTEGER) AS recency_days,
           NTILE(5) OVER (ORDER BY julianday(a.last_order_date) ASC) AS r_score,
           NTILE(5) OVER (ORDER BY a.frequency ASC)                  AS f_score,
           NTILE(5) OVER (ORDER BY a.monetary ASC)                   AS m_score
    FROM agg a CROSS JOIN ref r
),
seg AS (
    SELECT *,
        -- Canonical segment ladder (matches src/customer_segmentation.py).
        CASE
            WHEN m_score >= 4 AND f_score >= 4 AND r_score >= 3 THEN 'VIP'
            WHEN r_score <= 2 AND (f_score >= 3 OR m_score >= 4) THEN 'Clientes en riesgo'
            WHEN r_score <= 2                                    THEN 'Clientes inactivos'
            WHEN f_score <= 2 AND r_score >= 3                   THEN 'Nuevos clientes'
            ELSE 'Clientes frecuentes'
        END AS rfm_segment
    FROM rfm
)
SELECT
    rfm_segment,
    COUNT(*)                          AS customers,
    ROUND(AVG(recency_days), 1)       AS avg_recency_days,
    ROUND(AVG(frequency), 2)          AS avg_frequency,
    ROUND(SUM(monetary), 2)           AS total_monetary,
    ROUND(AVG(monetary), 2)           AS avg_monetary,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_customers
FROM seg
GROUP BY rfm_segment
ORDER BY total_monetary DESC;

-- name: customers_at_risk
-- PREGUNTA DE NEGOCIO:
--   ¿Qué clientes valiosos están dejando de comprar y deberían recuperarse?
-- COLUMNAS: recency_days, frequency, monetary, scores.
-- ORDEN: monetary DESC (priorizar recuperación por valor).
-- CONSIDERACIONES: coincide con el segmento 'Clientes en riesgo' de la escalera
--   canónica: baja recencia (r_score <= 2) con historial de compra relevante
--   (f_score >= 3 O m_score >= 4).
WITH line AS (
    SELECT customer_id, order_id, order_date,
           (quantity*unit_price - discount_amount + shipping_revenue) AS revenue, refund_amount
    FROM fact_sales
),
agg AS (
    SELECT customer_id, MAX(order_date) AS last_order_date,
           COUNT(DISTINCT order_id) AS frequency, SUM(revenue - refund_amount) AS monetary
    FROM line GROUP BY customer_id
),
ref AS (SELECT MAX(order_date) AS analysis_date FROM fact_sales),
rfm AS (
    SELECT a.customer_id, a.frequency, ROUND(a.monetary, 2) AS monetary,
           CAST(julianday(r.analysis_date) - julianday(a.last_order_date) AS INTEGER) AS recency_days,
           NTILE(5) OVER (ORDER BY julianday(a.last_order_date) ASC) AS r_score,
           NTILE(5) OVER (ORDER BY a.frequency ASC)                  AS f_score,
           NTILE(5) OVER (ORDER BY a.monetary ASC)                   AS m_score
    FROM agg a CROSS JOIN ref r
)
SELECT
    c.customer_id, c.customer_segment, c.region,
    rfm.recency_days, rfm.frequency, rfm.monetary,
    rfm.r_score, rfm.f_score, rfm.m_score
FROM rfm
JOIN dim_customer c ON rfm.customer_id = c.customer_id
WHERE rfm.r_score <= 2 AND (rfm.f_score >= 3 OR rfm.m_score >= 4)
ORDER BY rfm.monetary DESC;
