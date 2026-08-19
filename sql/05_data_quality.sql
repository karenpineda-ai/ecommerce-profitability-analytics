-- ==========================================================================
-- 05 · DATA QUALITY
-- Datos SIMULADOS y ya limpios (Fase 3) + con restricciones en el esquema
-- (Fase 4). Estas consultas verifican la integridad ON THE DATABASE y deben
-- devolver 0 incidencias, demostrando que el modelo está sano.
-- ==========================================================================

-- name: quality_checks
-- PREGUNTA DE NEGOCIO:
--   ¿La base cumple las reglas de calidad (nulos, huérfanos, rangos, fechas)?
-- COLUMNAS: check_name (regla) e issues (nº de incidencias; 0 = OK).
-- ORDEN: issues DESC (cualquier problema aparece primero).
-- CONSIDERACIONES: la limpieza reemplazó nulos descriptivos por 'Unknown', por lo
--   que los conteos de nulos deben ser 0. Los huérfanos son imposibles por las FK.
SELECT 'null_key_customer_id'  AS check_name, COUNT(*) AS issues FROM fact_sales WHERE customer_id IS NULL
UNION ALL SELECT 'null_key_product_id',       COUNT(*) FROM fact_sales WHERE product_id IS NULL
UNION ALL SELECT 'null_customer_city',        COUNT(*) FROM dim_customer WHERE city IS NULL
UNION ALL SELECT 'null_customer_region',      COUNT(*) FROM dim_customer WHERE region IS NULL
UNION ALL SELECT 'null_product_brand',        COUNT(*) FROM dim_product WHERE brand IS NULL
UNION ALL SELECT 'null_product_subcategory',  COUNT(*) FROM dim_product WHERE subcategory IS NULL
UNION ALL SELECT 'orphan_sales_customer',     COUNT(*) FROM fact_sales f LEFT JOIN dim_customer d ON f.customer_id=d.customer_id WHERE d.customer_id IS NULL
UNION ALL SELECT 'orphan_sales_product',      COUNT(*) FROM fact_sales f LEFT JOIN dim_product  p ON f.product_id =p.product_id  WHERE p.product_id  IS NULL
UNION ALL SELECT 'orphan_sales_channel',      COUNT(*) FROM fact_sales f LEFT JOIN dim_channel  c ON f.channel_id =c.channel_id  WHERE c.channel_id  IS NULL
UNION ALL SELECT 'orphan_sales_date',         COUNT(*) FROM fact_sales f LEFT JOIN dim_date     d ON f.order_date =d.date        WHERE d.date        IS NULL
UNION ALL SELECT 'orphan_marketing_channel',  COUNT(*) FROM fact_marketing m LEFT JOIN dim_channel c ON m.channel_id=c.channel_id WHERE c.channel_id IS NULL
UNION ALL SELECT 'quantity_le_zero',          COUNT(*) FROM fact_sales WHERE quantity <= 0
UNION ALL SELECT 'negative_amounts',          COUNT(*) FROM fact_sales
    WHERE unit_price < 0 OR discount_amount < 0 OR product_cost < 0
       OR shipping_cost < 0 OR payment_fee < 0 OR refund_amount < 0
UNION ALL SELECT 'dates_out_of_period',       COUNT(*) FROM fact_sales
    WHERE order_date < (SELECT MIN(date) FROM dim_date)
       OR order_date > (SELECT MAX(date) FROM dim_date)
UNION ALL SELECT 'margin_gt_100pct',          COUNT(*) FROM (
        SELECT (quantity*unit_price - discount_amount + shipping_revenue) AS revenue,
               (quantity*unit_price - discount_amount + shipping_revenue)
                   - product_cost - shipping_cost - payment_fee - refund_amount AS gp
        FROM fact_sales
    ) WHERE revenue > 0 AND gp / revenue > 1.0
ORDER BY issues DESC, check_name;

-- name: table_totals
-- PREGUNTA DE NEGOCIO:
--   ¿Coinciden los totales básicos de la base con lo esperado?
-- COLUMNAS: conteos por tabla y totales de negocio (revenue, gross_profit).
-- ORDEN: fila única (resumen).
-- CONSIDERACIONES: sirve para reconciliar contra data/processed/ y contra las
--   verificaciones de la Fase 4.
SELECT
    (SELECT COUNT(*) FROM dim_date)              AS dim_date_rows,
    (SELECT COUNT(*) FROM dim_product)           AS dim_product_rows,
    (SELECT COUNT(*) FROM dim_customer)          AS dim_customer_rows,
    (SELECT COUNT(*) FROM dim_channel)           AS dim_channel_rows,
    (SELECT COUNT(*) FROM fact_sales)            AS fact_sales_rows,
    (SELECT COUNT(*) FROM fact_marketing)        AS fact_marketing_rows,
    (SELECT COUNT(DISTINCT order_id) FROM fact_sales) AS distinct_orders,
    ROUND((SELECT SUM(quantity*unit_price - discount_amount + shipping_revenue)
           FROM fact_sales), 2)                  AS total_revenue,
    ROUND((SELECT SUM((quantity*unit_price - discount_amount + shipping_revenue)
                      - product_cost - shipping_cost - payment_fee - refund_amount)
           FROM fact_sales), 2)                  AS total_gross_profit;
