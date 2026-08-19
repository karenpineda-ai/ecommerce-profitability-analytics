# 📊 De los datos a las decisiones rentables — E-commerce Profitability Analytics

**Caso de estudio de portafolio · Business Analytics / Data Analytics**

> ⚠️ *Proyecto demostrativo con **datos 100% simulados** (semilla fija). No representan a
> ninguna empresa real; su fin es mostrar cómo trabajo un problema de negocio de punta a punta.*

---

## El reto

Un e-commerce puede **facturar mucho y ganar poco**. La pregunta que quise responder no
fue *"¿cuánto vendemos?"* sino **"¿dónde ganamos y dónde perdemos margen, y qué hacemos
al respecto?"**.

Para ello construí un pipeline completo y reproducible sobre un dataset simulado de
**18 meses, 20,000 pedidos y 3,000 clientes**, y lo llevé hasta recomendaciones para la
dirección.

## Qué hice (enfoque end-to-end)

1. **Generé** un dataset realista (estacionalidad, márgenes por categoría, devoluciones,
   descuentos, logística e inversión de marketing) con una semilla fija → 100% reproducible.
2. **Limpié y validé** los datos con **15 chequeos de calidad** automatizados.
3. Modelé un **esquema estrella** y lo cargué en **SQLite**.
4. Respondí las preguntas de negocio con **SQL** y **Python (pandas)**.
5. Segmenté clientes con **RFM** y preparé un modelo listo para **Power BI (DAX)**.
6. Sinteticé todo en un **informe ejecutivo** para dirección.

## Herramientas

`SQL` · `Python (pandas, numpy, matplotlib)` · `SQLite` · `Power BI (DAX)` · `pytest` · `Git`

## Los 3 insights que cambian la conversación

📌 **1. El revenue engaña.** *Electronics* era la categoría de **mayor facturación (7.3 M,
más de la mitad del total)**… y sin embargo **perdía dinero** (margen negativo). El
volumen escondía una fuga de margen.

📌 **2. Publicidad que resta.** Dos canales pagados tenían **contribución neta negativa**
tras descontar su inversión (−262 K y −163 K), mientras el **email** rendía un **ROAS de
23.6** y el crecimiento **orgánico** sostenía el beneficio real.

📌 **3. Todos los huevos en pocas canastas.** **10 productos concentraban el 75% del
beneficio** — un solo producto, más del 26%. Rentabilidad alta, pero frágil.

## Recomendaciones de negocio

- Rescatar el margen de las categorías que pierden (precios, costos, surtido).
- Reasignar presupuesto de los canales pagados ineficientes hacia email y orgánico.
- Proteger los productos núcleo y diversificar la base rentable.
- Poner topes de descuento y revisar el envío gratis.
- Retener a los clientes *VIP* y recuperar a los que están *en riesgo*.

## Lo que me llevo

- **El margen bruto cuenta la verdad que el revenue oculta.** Analizar rentabilidad —no
  solo ventas— cambia por completo las prioridades de la gerencia.
- **La reproducibilidad no es opcional:** semilla fija + validaciones + pruebas hacen que
  cualquiera pueda recrear los resultados y confiar en ellos.
- **El valor está en la traducción:** convertir 12 millones de filas en **cinco decisiones
  claras** para un gerente no técnico es el verdadero entregable.

---

🔗 *Repositorio con código, SQL, informe y especificación del dashboard.*
👤 **Karen Pineda** — Business Analyst / Data Analyst · 📧 pineda.karen@gmail.com

#DataAnalytics #BusinessIntelligence #SQL #Python #PowerBI #Ecommerce #Analytics
