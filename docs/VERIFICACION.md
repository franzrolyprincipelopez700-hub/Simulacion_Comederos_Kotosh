# Verificación ejecutada

## Guía completa y entrega portable

La suite frontend completa pasó **10 pruebas** en 33,7 s: incluye navegación del manual, búsqueda sin acentos del glosario, preguntas desplegables, accesos a configuración/comparación y diseño de escritorio/móvil sin desbordamiento de página. TypeScript y Vite compilan; se revisaron capturas a 1440 y 390 px.

Se exportó PostgreSQL con `pg_dump` custom, sin propietario ni privilegios. `scripts/verify_backup.py` restauró la copia en una base temporal de nombre único, comprobó revisión Alembic y conteos contra el manifiesto, verificó el balance de las réplicas, consultó salud e historial por la API y comprobó que una segunda restauración sobre datos existentes se rechaza. La base temporal se retiró al terminar. El inventario exacto y SHA-256 están en `database/simulador_avicola.manifest.json`.

Las instrucciones de descarga e instalación están en `LEEME_INSTALACION.txt` y README, con rutas relativas a la carpeta descargada. Se revisó la exclusión de `.env`, credenciales locales, entornos y dependencias instaladas antes de publicar.

Revisión de interfaz posterior: **8 pruebas frontend aprobadas** (5 flujos de navegador y 3 casos de decisiones). Se comprobó retirada de avisos repetidos, ayuda con hover/clic/Escape, conversión de porcentajes a fracciones internas, límites y filtros, empates numéricos, rangos conservadores y diseño de escritorio/tableta. TypeScript y build Vite pasan. El motor y las jornadas guardadas permanecen sin cambios.

Verificado en la computadora del usuario el **8 de octubre de 2026**, zona America/Lima. Entorno: Windows (cadena de plataforma `Windows-10-10.0.26200-SP0`), Python 3.10.8, Node 24.17.0, npm 11.13.0, PostgreSQL 18 local, Chrome instalado. Se utilizó el entorno virtual del proyecto, sin sustituir PostgreSQL por SQLite.

## Evidencia

| Comprobación | Resultado ejecutado |
|---|---|
| Motor/backend: suite pytest | 27 pruebas pasaron en la ejecución final; incluye persistencia de planificación de campo |
| Plan de campo | Persistencia en PostgreSQL y rechazo de valores inválidos, incluido en la suite |
| Navegador Playwright | 3 flujos pasaron; crear/guardar/ejecutar/reproducir/exportar, comparación e importación inválida, escritorio/tableta |
| Frontend | TypeScript y build Vite correctos, activos separados para gráficos |
| Dependencias frontend | `npm audit`: 0 vulnerabilidades reportadas tras actualizar Vite y dependencias transitivas |
| Base local | Conexión real, `simulador_avicola` creada si faltaba, migraciones aplicadas |
| Migración limpia | 001 → 002 → 003 en base temporal PostgreSQL vacía; 10 tablas contando Alembic; solo se retiró esa base temporal propia |
| Reinicio | API/trabajador reiniciados con los scripts; mismo ID del piloto, 390 réplicas completas conservadas |
| CSV, Excel y PDF | Generados desde réplicas guardadas; XLSX reabierto con openpyxl y PDF leído con pypdf |
| Reporte PDF | Renderizado con Poppler y revisado visualmente; 10 páginas del piloto, títulos/tablas/gráfico legibles |
| Escritorio/tableta | Capturas de 1440 px y 768 px inspeccionadas; sin desbordamiento horizontal en Inicio |
| Arranque | API, trabajador y frontend separados, localhost; script PowerShell probado |

El aviso de deprecación de Starlette sobre TestClient/httpx no impidió las pruebas. Playwright usa Chrome instalado; una descarga inicial del navegador de pruebas no completó y se detuvo, por lo que no se afirma que esa instalación adicional funcionara. Poppler emitió un aviso de fuente Symbol; las páginas se renderizaron y el gráfico y texto se inspeccionaron. No hay errores de integración en los flujos ejecutados. Las pruebas no equivalen a una validación de campo ni a una auditoría exhaustiva de accesibilidad.

## Casos numéricos y de integración cubiertos

Una jornada manual pequeña: 1 kg inicial, 3 kg/h durante 10 min → 0,5 kg consumido, 0,5 kg final, cero tiempo sin acceso, sin recargas ni trabajo. Conservación con las tres políticas, reserva y entradas externas, pérdidas, límites físicos en todos los estados, una persona sin actividades superpuestas, detección de P2 en inspección posterior al cruce, no duplicación de solicitudes, reserva agotada sin ciclos infinitos, alimento bloqueado, interrupción vacío + obstrucción contada una sola vez, denominador cero, atención al cierre excluida y trabajo truncado, reproducibilidad e independencia entre réplicas, demanda idéntica en bloques emparejados, Holm y análisis de diferencias por jornadas.

Integración: versiones inmutables y nueva sesión SQLAlchemy, resultados paginados, exportaciones parseables, cancelación pendiente y durante trabajo entre réplicas, rechazo de exportaciones parciales, recuperación de heartbeat vencido y reintento completo, rechazo de condiciones externas incompatibles, importación inválida y duplicada, rechazo de validar datos sintéticos, reserva de jornadas sin mezcla de particiones, persistencia de criterios/comparaciones, dos trabajadores sin duplicar una réplica y plan de recolección editable persistente.

## Rendimiento observado del piloto

- Tamaño: **13 alternativas × 30 réplicas = 390 jornadas**, cada una de 480 min, 3 comederos y paso de 1 min.
- Detalle: una réplica por alternativa conserva eventos/serie; las 390 conservan indicadores, semillas, períodos y actividades.
- Tiempo del trabajador, incluido guardado: **7,7474 s**.
- Tiempo observado desde encolado hasta detectar completado: **8,1813 s** (sondeo cada 0,4 s).
- Entorno: Windows, Python 3.10.8, PostgreSQL local. No es un benchmark general; no extrapolar a otra máquina o a réplicas mucho mayores.
- Evidencia reproducible local: `output/pilot-results.json`. Exportaciones: `output/piloto-kotosh.csv`, `.xlsx`, `.pdf`. Comando: `scripts/pilot.py` con el trabajador iniciado.

El piloto usa datos sintéticos y los resultados no se modificaron para favorecer una política. En este conjunto la continuidad está dominada por la incidencia preparada, y varias alternativas tienen la misma media de tiempo sin acceso; sus diferencias de trabajo y pérdidas sí varían. Los contrastes t con diferencias sin variabilidad figuran como no calculables. Sin límites operativos el resultado es descriptivo.

## Sensibilidad de resolución

`scripts/resolution.py` ejecutó las tres políticas en modo determinista con pasos de 2, 1, 0,5 y 0,25 min. P0/P1: tiempo sin acceso 5,3333 min/comedero en los cuatro pasos. P2: 19,3333; 17; 16,5; 16,25. Consumo total 5,76 kg; recargas y trabajo iguales en las resoluciones probadas. El paso inicial de 1 minuto tiene sesgo temporal visible respecto a pasos más pequeños: es una limitación declarada y se ofrece análisis de sensibilidad en la interfaz.

## Límites pendientes reales

- No hay mediciones de campo ni validación contra jornadas reales. Capacidad efectiva, consumo, pérdidas, obstrucciones y tiempos requieren medición y procedencia individual.
- La calibración es manual. Validación disponible compara indicadores observados reservados contra P0 y guarda tolerancias/errores; no ajusta parámetros, no certifica el modelo y requiere comprobar comparabilidad del protocolo.
- El consumo se representa como demandas puntuales por paso; interrupciones dentro de un paso se aproximan. No se declara convergencia universal.
- Las opciones avanzadas se editan mediante JSON validado. No hay editor visual específico de distribuciones empíricas, aunque hay variación uniforme acotada y perfil de demanda.
- CSV es el formato de importación; Excel es exportación de resultados. Actividades que cruzan medianoche deben dividirse por fecha.
- Las cancelaciones se aplican entre réplicas. Recuperación detecta interrupción y permite reiniciar; no guarda estado interno SimPy para continuar desde el minuto intermedio.
- No se ejecutaron pruebas de carga masiva, funcionamiento remoto o publicación. La aplicación fue diseñada y comprobada para localhost y un espacio de trabajo.
