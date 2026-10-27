# Data Analytics — Farmacia y Perfumería

Proyecto de portfolio de Data Analytics con datos sintéticos de farmacia. Incluye generación reproducible de datos, controles de calidad, KPIs comerciales, alertas simples de stock y consultas SQL ejecutables.

![Pharmacy Analytics CI](https://github.com/agustiininicabral/data-analytics-farmacia-farmafe/actions/workflows/ci.yml/badge.svg)

## Qué demuestra

- Perfilado y validación de datos con claves únicas y relaciones entre tablas.
- Cálculo de ventas brutas, descuentos, ventas netas, costo de mercadería, beneficio bruto y margen.
- Análisis mensual, por categoría y por canal.
- Detección de productos en o por debajo del punto de reposición.
- Consultas SQL en SQLite en memoria.
- Pruebas automáticas y artefactos reproducibles en GitHub Actions.

**Datos:** todos los registros son sintéticos. No se utilizan datos de Farmafe ni información real de clientes o transacciones.

## Requisitos

- Python 3.12 o posterior.
- No hay dependencias externas: el pipeline usa la biblioteca estándar de Python y SQLite.

## Inicio rápido en Windows PowerShell

Desde la raíz del repositorio:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python scripts/generate_data.py
python scripts/run_analysis.py
python scripts/run_sql.py
python -m unittest discover -s tests -v
```

La generación crea los archivos CSV bajo `data/raw/`. El análisis escribe KPIs y reportes en `outputs/`; las consultas SQL exportan sus resultados en `outputs/sql/`. Los datos generados no se versionan.

## Datos generados

- `products.csv`: ID, nombre, categoría, marca, precio, costo y punto de reposición.
- `sales.csv`: transacción, fecha, producto, cantidad, precio/costo al momento de la venta, descuento, canal y región.
- `inventory.csv`: stock al 31 de diciembre de 2025 por producto.

Para reproducir otra muestra:

```powershell
python scripts/generate_data.py --seed 2026 --sales 1200 --products 60
```

El mismo seed y los mismos parámetros generan los mismos registros.

## KPIs y reglas

- Ventas brutas = cantidad × precio unitario.
- Descuento = ventas brutas × porcentaje de descuento.
- Ventas netas = ventas brutas − descuento.
- Costo de mercadería = cantidad × costo unitario.
- Beneficio bruto = ventas netas − costo de mercadería.
- Margen bruto % = beneficio bruto / ventas netas.
- Alerta de stock = stock disponible menor o igual al punto de reposición.

El validador comprueba IDs duplicados, referencias a productos inexistentes, fechas inválidas, cantidades no positivas, precios/costos inválidos, descuentos fuera de rango y stock negativo. El análisis se detiene si la fuente no pasa las reglas.

## SQL

Las consultas de `sql/analysis.sql` calculan ventas mensuales, rendimiento por categoría y canal, y alertas de reposición. El runner carga los CSV en una base SQLite temporal, ejecuta las consultas con nombre y exporta un CSV por consulta.

## Salidas

- `outputs/kpi_report.json`: KPIs y resúmenes estructurados.
- `outputs/REPORT.md`: resumen ejecutivo y archivos generados.
- `outputs/monthly_sales.csv`: evolución mensual.
- `outputs/category_sales.csv`: ventas y beneficio por categoría.
- `outputs/channel_sales.csv`: ventas por canal.
- `outputs/stock_alerts.csv`: productos que alcanzan el umbral de reposición.
- `outputs/sql/`: resultados de las consultas SQL.

GitHub Actions ejecuta los tests, genera la muestra, produce los reportes y publica un artefacto temporal. Las cifras son demostrativas y no deben usarse como pronósticos o recomendaciones comerciales reales.

## Estructura

- `src/pharmacy_analytics.py`: generación, validación, análisis y reportes.
- `scripts/generate_data.py`: generador CLI.
- `scripts/run_analysis.py`: validación y KPIs.
- `scripts/run_sql.py`: ejecución de SQL en SQLite.
- `sql/analysis.sql`: consultas analíticas.
- `tests/test_pipeline.py`: pruebas de reproducibilidad, reglas, KPIs y SQL.

## Limitaciones

- No se modelan recetas, pacientes, información clínica ni medicamentos sujetos a prescripción.
- Las alertas de stock son umbrales estáticos, no una predicción de demanda.
- El beneficio bruto no incluye salarios, alquiler, impuestos ni otros costos operativos.
- Los precios y costos son ficticios y no representan una moneda real.

## Licencia

MIT. Consultá [LICENSE](LICENSE).
