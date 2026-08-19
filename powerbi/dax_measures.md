# Medidas DAX — E-commerce Profitability Analytics

> **Datos simulados.** Estas medidas asumen el modelo estrella documentado en
> [`data_dictionary.md`](data_dictionary.md): `fact_sales` y `fact_marketing`
> relacionadas con `dim_date`, `dim_product`, `dim_customer`, `dim_channel`.
>
> **Requisitos del modelo:**
> 1. Marcar `dim_date` como **tabla de fechas** (Modelado → Marcar como tabla de fechas → `dim_date[date]`).
> 2. Relación activa `dim_date[date]` → `fact_sales[order_date]` y `dim_date[date]` → `fact_marketing[date]`.
> 3. Relación **inactiva** `dim_date[date]` → `dim_customer[acquisition_date]` (para "New Customers"/CAC).
> 4. Crear una tabla `_Measures` (tabla vacía) donde alojar todas las medidas.

Convención: `[Medida]` referencia otra medida; los nombres de columna usan
`tabla[columna]`.

---

## Medidas base (helpers)

Se definen primero porque el resto las reutiliza (una sola fuente de verdad para
las fórmulas de CLAUDE.md).

### Revenue
- **Fórmula DAX:**
  ```DAX
  Revenue =
  SUMX (
      fact_sales,
      fact_sales[quantity] * fact_sales[unit_price]
          - fact_sales[discount_amount]
          + fact_sales[shipping_revenue]
  )
  ```
- **Tabla y columnas:** `fact_sales[quantity, unit_price, discount_amount, shipping_revenue]`.
- **Resultado esperado:** ingreso bruto tras descuentos e incluyendo envío. Total del modelo ≈ 12.417.781 (datos simulados).
- **Problemas de contexto:** es un `SUMX` con contexto de fila por línea; correcto a cualquier grano (mes, categoría, canal). No restar aquí las devoluciones (van en Gross Profit).

### Product Cost
- **Fórmula DAX:** `Product Cost = SUM ( fact_sales[product_cost] )`
- **Columnas:** `fact_sales[product_cost]` (ya es `quantity × unit_cost`).
- **Resultado esperado:** costo de la mercancía vendida.
- **Problemas de contexto:** no confundir con `unit_cost` (unitario, está en `dim_product`).

### Shipping Cost / Payment Fee / Refund Amount
- **Fórmula DAX:**
  ```DAX
  Shipping Cost = SUM ( fact_sales[shipping_cost] )
  Payment Fee   = SUM ( fact_sales[payment_fee] )
  Refund Amount = SUM ( fact_sales[refund_amount] )
  ```
- **Columnas:** las homónimas de `fact_sales`.
- **Resultado esperado:** componentes de costo restados en Gross Profit.
- **Problemas de contexto:** `Refund Amount` solo es > 0 en líneas con `returned_flag = 1`.

---

## 1. Gross Profit
- **Fórmula DAX:**
  ```DAX
  Gross Profit = [Revenue] - [Product Cost] - [Shipping Cost] - [Payment Fee] - [Refund Amount]
  ```
- **Tabla y columnas:** deriva de `fact_sales` vía medidas base.
- **Resultado esperado:** utilidad bruta tras costo, logística, comisión y devoluciones. Total ≈ 1.111.339.
- **Problemas de contexto:** puede ser **negativo** en categorías de bajo margen (Electronics, Grocery); es correcto, no un error.

## 2. Gross Margin %
- **Fórmula DAX:** `Gross Margin % = DIVIDE ( [Gross Profit], [Revenue] )`
- **Columnas:** medidas `[Gross Profit]`, `[Revenue]`.
- **Resultado esperado:** porcentaje (formatear como %). Global ≈ 8,9%.
- **Problemas de contexto:** `DIVIDE` evita división por cero (devuelve BLANK). No promediar márgenes por fila: siempre recalcular como cociente de sumas.

## 3. Orders
- **Fórmula DAX:** `Orders = DISTINCTCOUNT ( fact_sales[order_id] )`
- **Columnas:** `fact_sales[order_id]`.
- **Resultado esperado:** nº de pedidos (no líneas). Total = 20.000.
- **Problemas de contexto:** un pedido con varias líneas cuenta **una** vez; al filtrar por producto, un pedido puede contarse en varios productos.

## 4. Units Sold
- **Fórmula DAX:** `Units Sold = SUM ( fact_sales[quantity] )`
- **Columnas:** `fact_sales[quantity]`.
- **Resultado esperado:** unidades vendidas. Total = 61.434.
- **Problemas de contexto:** incluye unidades de líneas devueltas (la devolución se refleja en Gross Profit, no aquí).

## 5. Average Order Value (AOV)
- **Fórmula DAX:** `Average Order Value = DIVIDE ( [Revenue], [Orders] )`
- **Columnas:** medidas `[Revenue]`, `[Orders]`.
- **Resultado esperado:** ticket promedio ≈ 621.
- **Problemas de contexto:** carece de sentido en un contexto solo-marketing (sin pedidos). Al filtrar por producto, el AOV se distorsiona (numerador parcial, denominador = pedidos con ese producto).

## 6. Marketing Spend
- **Fórmula DAX:** `Marketing Spend = SUM ( fact_marketing[marketing_spend] )`
- **Columnas:** `fact_marketing[marketing_spend]`.
- **Resultado esperado:** inversión de marketing. Solo canales pagados (Paid Search, Social Ads, Email, Referral).
- **Problemas de contexto:** al cruzar con `dim_product` da BLANK (marketing no tiene grano de producto). Usar en contexto de fecha/canal.

## 7. New Customers
- **Fórmula DAX:**
  ```DAX
  New Customers =
  CALCULATE (
      DISTINCTCOUNT ( dim_customer[customer_id] ),
      USERELATIONSHIP ( dim_customer[acquisition_date], dim_date[date] )
  )
  ```
- **Tabla y columnas:** `dim_customer[customer_id, acquisition_date]`, `dim_date[date]`.
- **Resultado esperado:** clientes adquiridos en el periodo filtrado (por canal si `dim_channel` filtra vía `acquisition_channel`).
- **Problemas de contexto:** **requiere** la relación inactiva acq_date→date; sin `USERELATIONSHIP` cuenta por fecha de pedido (incorrecto). El vínculo con canal usa `dim_customer[acquisition_channel]`, no la relación de ventas.

## 8. CAC (Customer Acquisition Cost)
- **Fórmula DAX:** `CAC = DIVIDE ( [Marketing Spend], [New Customers] )`
- **Columnas:** medidas `[Marketing Spend]`, `[New Customers]`.
- **Resultado esperado:** costo por cliente nuevo, por canal (p. ej. Paid Search ≈ 1.100).
- **Problemas de contexto:** BLANK en canales sin spend (Organic/Direct). La atribución `spend`↔`new customers` por canal es una simplificación (single-touch).

## 9. ROAS (Return on Ad Spend)
- **Fórmula DAX:** `ROAS = DIVIDE ( [Revenue], [Marketing Spend] )`
- **Columnas:** medidas `[Revenue]`, `[Marketing Spend]`.
- **Resultado esperado:** revenue por unidad invertida (p. ej. Email ≈ 24, Paid Search ≈ 5).
- **Problemas de contexto:** revenue y spend deben compartir el mismo filtro de `dim_channel`. BLANK sin spend. Atribución single-touch (limitación).

## 10. Net Marketing Contribution
- **Fórmula DAX:** `Net Marketing Contribution = [Gross Profit] - [Marketing Spend]`
- **Columnas:** medidas `[Gross Profit]`, `[Marketing Spend]`.
- **Resultado esperado:** utilidad tras marketing; **negativa** en canales pagados poco eficientes.
- **Problemas de contexto:** en canales sin spend equivale al Gross Profit. Interpretar por canal, no a nivel producto.

## 11. Return Rate
- **Fórmula DAX:**
  ```DAX
  Returned Orders =
  CALCULATE ( DISTINCTCOUNT ( fact_sales[order_id] ), fact_sales[returned_flag] = 1 )

  Return Rate = DIVIDE ( [Returned Orders], [Orders] )
  ```
- **Tabla y columnas:** `fact_sales[order_id, returned_flag]`.
- **Resultado esperado:** % de pedidos con al menos una línea devuelta (mayor en Fashion).
- **Problemas de contexto:** definido a **nivel de pedido**; una versión a nivel línea usaría `COUNTROWS`. Documentar cuál se muestra.

## 12. Repeat Purchase Rate
- **Fórmula DAX:**
  ```DAX
  Customers With Orders = DISTINCTCOUNT ( fact_sales[customer_id] )

  Repeat Customers =
  COUNTROWS (
      FILTER (
          VALUES ( fact_sales[customer_id] ),
          CALCULATE ( DISTINCTCOUNT ( fact_sales[order_id] ) ) >= 2
      )
  )

  Repeat Purchase Rate = DIVIDE ( [Repeat Customers], [Customers With Orders] )
  ```
- **Tabla y columnas:** `fact_sales[customer_id, order_id]`.
- **Resultado esperado:** % de clientes con 2+ pedidos.
- **Problemas de contexto:** el `FILTER` sobre `VALUES` puede ser costoso en modelos grandes; el resultado depende del rango de fechas del contexto (clientes con 2+ pedidos *dentro* del filtro).

## 13. Revenue Growth (MoM %)
- **Fórmula DAX:**
  ```DAX
  Revenue PM = CALCULATE ( [Revenue], DATEADD ( dim_date[date], -1, MONTH ) )

  Revenue Growth % = DIVIDE ( [Revenue] - [Revenue PM], [Revenue PM] )
  ```
- **Tabla y columnas:** `dim_date[date]`, medida `[Revenue]`.
- **Resultado esperado:** crecimiento mensual (pico +22,8% en dic; caída −39,9% en ene).
- **Problemas de contexto:** exige `dim_date` **marcada como tabla de fechas** y fechas contiguas. BLANK en el primer mes. Usar en granularidad de mes (no día/año).

## 14. Gross Profit Growth (MoM %)
- **Fórmula DAX:**
  ```DAX
  Gross Profit PM = CALCULATE ( [Gross Profit], DATEADD ( dim_date[date], -1, MONTH ) )

  Gross Profit Growth % = DIVIDE ( [Gross Profit] - [Gross Profit PM], [Gross Profit PM] )
  ```
- **Tabla y columnas:** `dim_date[date]`, medida `[Gross Profit]`.
- **Resultado esperado:** crecimiento mensual de la utilidad bruta.
- **Problemas de contexto:** si `[Gross Profit PM]` es negativo, el % de crecimiento se vuelve **contra-intuitivo** (dividir por un negativo); interpretar con cuidado o mostrar el delta absoluto.

---

## Medidas complementarias (opcionales, recomendadas)

### Revenue per Customer
```DAX
Revenue per Customer = DIVIDE ( [Revenue], [Customers With Orders] )
```
Valor medio por cliente activo.

### Average Discount %
```DAX
Average Discount % =
DIVIDE ( SUM ( fact_sales[discount_amount] ),
         SUMX ( fact_sales, fact_sales[quantity] * fact_sales[unit_price] ) )
```
Descuento medio sobre precio de lista. *Contexto:* denominador = venta a precio de lista (sin descuento).

### CLV Aproximado
```DAX
CLV Approx = DIVIDE ( [Gross Profit], [Customers With Orders] )
```
Proxy simple de valor por cliente (gross profit por cliente). **Limitación:** no es un CLV probabilístico; no proyecta comportamiento futuro.

### Conversions
```DAX
Conversions = SUM ( fact_marketing[conversions] )
```
Conversiones atribuidas al marketing (grano canal-día-campaña). Usada en la página
*Marketing Performance*. *Contexto:* aplicar con `dim_channel`/`dim_date`; devuelve
BLANK al cruzar con `dim_product` (marketing no tiene grano de producto).

### Cost per Conversion
```DAX
Cost per Conversion = DIVIDE ( [Marketing Spend], [Conversions] )
```
Costo por conversión, por canal/campaña. *Contexto:* BLANK sin spend o sin
conversiones; comparar entre canales (Email el más eficiente, Social Ads el más caro).
`[Marketing Spend]` y `[Conversions]` deben compartir el mismo filtro de `dim_channel`.

---

## Notas transversales de contexto

- **Grano mixto:** `fact_sales` (línea de pedido) y `fact_marketing` (canal-día) solo
  se combinan a través de dimensiones compartidas (`dim_date`, `dim_channel`). Cruzar
  una medida de marketing con `dim_product` devuelve BLANK.
- **Devoluciones:** afectan `[Gross Profit]` (vía `Refund Amount`), no `[Revenue]` ni `[Units Sold]`.
- **Formato:** aplicar formato de moneda a montos y porcentaje a `%`; fijar decimales.
- Toda cifra de "Resultado esperado" proviene de los **datos simulados** (semilla 42).
