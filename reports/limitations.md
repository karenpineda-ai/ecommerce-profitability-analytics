# Limitaciones

> ⚠️ **Datos simulados — proyecto demostrativo.** Estas limitaciones acotan cómo deben
> interpretarse los resultados. El proyecto existe para demostrar competencias
> analíticas, no para orientar decisiones de un negocio real.

## Sobre los datos

- **Datos simulados:** los patrones (estacionalidad, márgenes, devoluciones) son
  generados por reglas en `src/config.py`; **no reflejan una empresa real** ni deben
  usarse para conclusiones de mercado.
- **Universo cerrado:** el dataset no incorpora competencia, macroeconomía, campañas
  externas, roturas de stock ni comportamiento de proveedores.
- **Volumen acotado:** 18 meses y 20,000 pedidos; series más largas darían estimaciones
  estacionales y de tendencia más robustas.

## Sobre el método

- **Atribución de único toque:** el crédito de cada venta va al canal del pedido, no a
  un recorrido multitáctil; ROAS y CAC pueden estar sobre/subestimados por canal.
- **CLV aproximado:** se usa el `monetary` acumulado como proxy de valor; no se modela
  probabilísticamente (p. ej. BG/NBD o Gamma-Gamma).
- **RFM descriptivo/histórico:** clasifica el comportamiento pasado; **no predice** la
  compra futura. Los cortes por quintil son relativos a esta base, no absolutos.
- **Umbrales convencionales:** "alto/bajo" margen y volumen se definen respecto al
  promedio; otros cortes cambiarían la lista de productos señalados.
- **Asociación, no causalidad:** relaciones como descuento↔margen son correlaciones
  observadas, no relaciones causales demostradas.

## Sobre el alcance técnico

- **Alcance analítico, no productivo:** SQLite y scripts por lotes; no es un sistema
  transaccional, no hay orquestación ni actualización incremental.
- **Moneda única** y sin ajuste por inflación.
- **Sin datos de costos fijos ni gastos generales:** el margen es **bruto**; no llega a
  resultado operativo ni neto.

## Cómo mitigar estas limitaciones

Ver [próximas mejoras en el README](../README.md#14-próximas-mejoras): atribución
multitáctil, CLV probabilístico, elasticidad precio–demanda y orquestación del pipeline.
