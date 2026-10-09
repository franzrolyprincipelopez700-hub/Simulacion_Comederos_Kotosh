# API y datos de campo

Contrato completo generado por FastAPI en `/docs` y `/openapi.json`. Prefijo `/api`, JSON UTF-8. No se transmiten credenciales de la base. El usuario local tiene un espacio de trabajo; sin autenticación y con puertos vinculados a loopback.

| Método / ruta | Uso |
|---|---|
| GET `/health`, `/overview`, `/default` | Conexión PostgreSQL, conteos y escenario sintético |
| POST `/validate` | Validar configuración antes de aplicarla |
| GET `/scenarios?q=&page=1` | 20 escenarios por página, versiones originales |
| POST `/scenarios?scenario_id=...` | Crear o añadir versión inmutable (cuerpo Scenario) |
| POST `/experiments` | Encolar configuraciones, nombre, exploratory y analysis_kind |
| GET `/experiments?q=&page=1` | Historial de 20 trabajos por página |
| GET `/experiments/{id}` | Estado, progreso, configuración, resultados e incidencias |
| POST `/experiments/{id}/cancel` | Cancelar pendiente inmediatamente o entre réplicas |
| POST `/experiments/{id}/retry` | Reiniciar fallido/cancelado desde cero |
| GET `/experiments/{id}/runs?page=1` | 50 réplicas, indicadores y actividades |
| GET `/runs/{id}/detail?offset=0&limit=1000` | Eventos y estados paginados, límite máximo 2000 |
| GET `/experiments/{id}/export/{csv,xlsx,pdf}` | Exportación de resultados completos |
| GET `/field/template` | Plantilla CSV vacía |
| GET / POST `/field/plan` | Planificación editable y persistente de jornadas de campo |
| POST `/field/preview` | Revisar filas sin persistir |
| POST `/field/import` | Incorporar solo un archivo completamente válido |
| GET `/datasets`, `/datasets/{id}?page=1` | Conjuntos y observaciones (100 por página) |
| POST `/validation` | Guardar criterios y comparación P0 contra datos observados reservados |
| GET `/validation/history` | Criterios y resultados guardados, últimas 100 comparaciones |

Un experimento contiene `configurations: Scenario[]`, `name`, `exploratory: bool` y `analysis_kind: paired|sensitivity`. La primera alternativa de una comparación múltiple es P0. Réplicas y semillas iguales dentro del bloque. Una comparación `paired` exige que solo difieran parámetros de tratamiento: política, horario, objetivo, umbral, intervalo, cantidad y demora. La sensibilidad permite distintas entradas y omite contrastes emparejados. Máximo 30 alternativas, 500 réplicas y un límite de 20 millones de unidades paso × comedero para evitar encargos locales excesivos.

Errores 422: parámetros inválidos, condiciones externas incompatibles, importación inválida o datos de validación no reservados/observados. 404: ID no encontrado. 409: estado incompatible, por ejemplo exportar incompleto o reintentar completado.

## Persistencia

PostgreSQL JSONB conserva configuraciones, semillas, versión del modelo, indicadores, actividades y observaciones. Tablas separadas para escenarios, versiones, experimentos, réplicas, detalle visual, conjuntos, observaciones y registros de validación. Claves foráneas, índices para fecha/estado/nombre y unicidad de versión, réplica y huella de observación. Eventos se guardan por réplica en JSONB y se consultan por páginas; no se conserva cada evento como fila independiente.

Un trabajador reclama una fila pendiente en transacción con `SELECT ... FOR UPDATE SKIP LOCKED`. Cambia a “en ejecución” antes de calcular y confirma el propietario. Guarda una réplica por transacción y actualiza progreso/heartbeat. Solo genera análisis definitivo al completar todas. Un error deja estado fallido y resultados parciales incompletos. Un proceso sin heartbeat durante 2 minutos se identifica como interrumpido y pasa a fallido cuando un trabajador realiza su revisión. El reintento elimina resultados parciales de ese trabajo y repite las semillas originales; no simula una reanudación intermedia. Cancelación entre réplicas; no aborta una réplica dentro del motor.

La carga visual se limita con `detail_replicates` (1 inicial, hasta 10). Las demás conservan indicadores, periodos y actividades. La UI carga todas las páginas del detalle seleccionado para poder recorrer el horizonte; la API limita cada respuesta. Una réplica muy grande todavía puede consumir memoria; el límite de experimento reduce el riesgo, pero esta no es una arquitectura de procesamiento distribuido masivo. El heartbeat se escribe entre réplicas: si se amplían límites para permitir una réplica que tarde más de 2 minutos, debe incorporarse heartbeat durante el cálculo antes de usar recuperación automática.

## Plantilla de campo

Columnas exactas (cabecera técnica estable, etiquetas del formulario en español):

```csv
date,time,feeder,kind,kg,end_time,value,notes
```

- `date`: AAAA-MM-DD; `time`: HH:MM. El formulario permite registrar cada observación sin editar CSV.
- `feeder`: identificación; `SISTEMA` para actividades compartidas e indicadores de jornada.
- `kind`: suministro, consumo, remanente, pérdida, inspección, recarga, actividad, interrupción o indicador.
- `kg`: masa no negativa cuando aplique; obligatoria para suministro, consumo, remanente y pérdida.
- `end_time`: HH:MM, posterior al inicio y el mismo día; obligatoria para actividad/interrupción.
- `value`: indicador completo de jornada, no negativo, cuando `kind=indicador`.
- `notes`: notas; para `indicador` debe ser `shortage`, `waste`, `refills` o `work`, usando sus unidades respectivas.

“Suministro” para validación del desperdicio debe contener existencias iniciales y entradas externas de la **misma frontera** del modelo, incluyendo reserva. Las recargas son transferencias, por lo que se cuentan con “recarga” sin sumarlas de nuevo al suministro. Las actividades de la persona se unen temporalmente para evitar superposición; las interrupciones se unen por comedero antes de obtener minutos/comedero. Registra todos los comederos usados en una jornada, también los que no tuvieron interrupciones (por ejemplo mediante remanentes). Un indicador explícito permite distinguir cero verificado de dato ausente.

El panel muestra errores por fila y duplicados antes de confirmar. Una huella canónica detecta duplicados dentro del archivo y del conjunto elegido. No se importan parcialmente filas buenas si hay errores. El origen es observado o sintético y la partición calibración/validación. Fechas observadas no pueden aparecer en ambas particiones. El separador es coma, decimal punto y codificación UTF-8 (BOM admitido). No se importa Excel en esta versión.

La validación calcula medias por jornada de indicadores disponibles, errores absolutos respecto a la media simulada de P0 y cumplimiento de tolerancias definidas en el formulario. Criterios y resultado quedan guardados. No calcula inferencia de equivalencia ni ajusta automáticamente parámetros. No acepta conjuntos sintéticos o usados para calibración. Requiere revisar manualmente que horizonte, comederos, lote, fronteras y protocolo de observación sean comparables. Nunca presenta “Modelo validado” automáticamente.

Ejemplo **sintético** para practicar; no usar como observado:

```csv
date,time,feeder,kind,kg,end_time,value,notes
2026-10-08,08:00,SISTEMA,suministro,11,,,Existencias iniciales incluyendo reserva
2026-10-08,08:10,C1,interrupción,,08:20,,Sin acceso
2026-10-08,08:15,SISTEMA,actividad,,08:25,,Desplazamiento y carga
2026-10-08,08:25,C1,recarga,1,,,
2026-10-08,16:00,C1,remanente,0.5,,,
2026-10-08,16:00,C2,remanente,0.5,,,
2026-10-08,16:00,C3,remanente,0.5,,,
2026-10-08,16:00,SISTEMA,pérdida,0.02,,,
```
