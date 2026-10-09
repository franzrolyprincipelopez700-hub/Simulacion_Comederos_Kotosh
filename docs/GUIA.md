# Guía para el responsable

## Propósito del sistema

El objetivo es mejorar la continuidad del alimento accesible en los comederos, manteniendo el desperdicio y el trabajo del responsable dentro de límites aceptables. Un comedero puede quedar vacío aunque haya reserva: importan la detección, el momento de atención y la duración de las actividades. El sistema compara esos compromisos; reducir trabajo es uno de los criterios, junto con continuidad y pérdidas.

El menú **Guía de uso** ofrece un manual con índice, recorrido de seis pasos, tabla de políticas, unidades y ejemplos de indicadores, criterios de decisión, registro de campo, accesos a las herramientas, preguntas frecuentes y glosario con búsqueda. Los botones abren las secciones correspondientes de la aplicación.

## Recorrido de trabajo

1. Abre Inicio y selecciona **Nueva simulación** o **Abrir demostración**. La demostración contiene supuestos sintéticos, no registros de una granja.
2. Identifica tus comederos y verifica capacidad efectiva y alimento inicial en kg. Configura el lote. La demanda pertenece al lote completo, no a cada ave individual.
3. Indica duración, ventana en que se requiere alimento, demanda potencial y reserva. En el panel avanzado puedes registrar entradas programadas y procedencia de valores.
4. Registra cuándo está disponible la persona y cuánto demora cada actividad.
5. Elige una política: referencia habitual P0, por horarios P1 o por nivel mínimo detectado en inspecciones P2.
6. Revisa, guarda y ejecuta. Guardar un escenario existente crea una versión. Una ejecución individual conserva su configuración original aunque luego la edites.
7. Mientras se calcula, revisa progreso. Al completar puedes reproducir, pausar o desplazar el reloj. La velocidad visual no cambia los resultados.
8. Consulta indicadores, balance, remanentes y solicitudes pendientes. Un comedero puede estar obstruido con alimento dentro; stock no equivale a acceso.
9. En Comparar alternativas ejecuta réplicas con condiciones iguales. Revisa todos los indicadores. Sin límites operativos no se declara ganadora. Conserva un piloto y confirma una elección con nuevas semillas.
10. Descarga el informe o recupera cualquier experimento desde Historial. Los datos viven en PostgreSQL y permanecen al cerrar el navegador.

## Ayudas y decisiones en la interfaz

Cada campo habitual tiene un círculo con `?`: pasa el puntero para leer qué ingresar, la unidad y un ejemplo. Haz clic para mantenerlo abierto; otro clic o Escape lo cierra. Los campos de llenado, umbral y pérdida se completan en **porcentaje** (80, 20, 2), aunque el motor conserva fracciones (0,8, 0,2, 0,02). En comparación, los objetivos y umbrales también usan porcentajes separados por comas.

En resultados, los accesos de sección llevan al resumen de decisiones, recorrido, indicadores y tabla comparativa. La lectura de una jornada identifica demanda no atendida, tiempo activo del responsable, remanentes, solicitudes al cierre y comederos con interrupciones. “Probar tres estrategias” ejecuta P0, P1 cada 90 minutos y P2 con inspección cada 30 minutos/umbral 20 %, usando las mismas condiciones externas y 30 jornadas por opción.

Cuando hay alternativas, “¿Qué opción encaja en tu jornada?” muestra continuidad, pérdida y trabajo. Introduce límites y decide si comprobarlos con los promedios o con la cota superior del intervalo. Elige qué priorizar cuando hay igual continuidad: ahorrar trabajo o reducir pérdidas. Los ajustes de esta revisión filtran los resultados almacenados; no cambian el cálculo original ni la configuración guardada del experimento. Una alternativa con mejor continuidad que exceda los límites queda fuera. La referencia también puede ser la opción a mantener.

El gráfico de puntos relaciona minutos de trabajo y tiempo sin alimento. El gráfico de barras compara pérdidas. La tabla filtra opciones que cumplen ambos límites y opciones no superadas simultáneamente en los tres indicadores. Diferencias de menos de 1e-8 en las medias se consideran empate numérico para esta ordenación; se conservan las medias originales. La elección operativa por medias y límites no sustituye los contrastes estadísticos, disponibles en el detalle.

## Glosario de indicadores

**Escenario:** condiciones y reglas de una jornada. **Réplica:** una jornada calculada con flujos aleatorios independientes de otras jornadas. **Experimento:** conjunto de réplicas y alternativas. **Demanda potencial:** masa que las aves requieren. **Consumo atendido:** masa tomada de comederos accesibles. **Reserva:** alimento disponible para abastecer. **Umbral:** nivel que permite solicitar reposición cuando se detecta en inspección. **Solicitud:** necesidad registrada que puede esperar; no equivale a una recarga completada. **IC:** intervalo de confianza de una media o diferencia. **DE:** variabilidad entre jornadas. **Calibración:** ajuste de supuestos/parámetros con datos destinados a ese fin. **Validación:** comparación con jornadas reservadas, bajo criterios previamente definidos; un resultado sintético no valida una granja.

## Guion de presentación a la docente (8–12 minutos)

- **Contexto, 1 min:** nombre del proyecto, problema de continuidad del alimento, límites del alcance sin sensores ni crecimiento biológico.
- **Supuestos, 2 min:** abrir demostración, mostrar 3 × 1,5 kg y etiqueta sintética; explicar capacidad pendiente de campo y procedencia en opciones avanzadas.
- **Jornada, 3 min:** ejecutar o abrir piloto guardado. Llevar reloj cerca de minuto 210; observar C2 obstruido con stock, reparación y recurso humano. Mostrar solicitud, espera, atención y recarga como eventos distintos. Pausar solo reproducción.
- **Resultados, 2 min:** explicar unidades de los indicadores, separar demanda/consumo/pérdida, comprobar balance y remanentes. Mostrar períodos sin acceso y actividades sin superposición.
- **Alternativas, 2 min:** abrir piloto 13 × 30, comparar trabajo/pérdidas/continuidad e IC. Declarar que 30 réplicas no garantizan precisión y que en este piloto no se definieron límites para recomendar ganadora. Señalar que el motor no modifica resultados para favorecer una política.
- **Trazabilidad, 1 min:** descargar PDF, abrir historial y datos de campo. Explicar planificación editable de 10 jornadas para calibración y 5 para validación aún no recogidas. Enseñar rechazo de una fila inválida y separación de jornadas completas.
- **Cierre:** indicar sensibilidad del paso temporal y futuras observaciones de la docente; señalar archivos separados de políticas, indicadores y parámetros.

## Si algo no funciona

Mensaje de conexión: inicia backend y revisa PostgreSQL/`.env`. Trabajo pendiente: inicia trabajador. Trabajo interrumpido: tras 2 minutos la revisión del trabajador lo marca fallido; usa Reintentar, que empieza desde cero. Puerto ocupado: comprueba aplicación existente, no cierres otros proyectos. Campos inválidos: corrige valores y ventanas antes de ejecutar. Informe no disponible: requiere estado completado. Detalle ausente: selecciona una de las primeras réplicas conservadas.
