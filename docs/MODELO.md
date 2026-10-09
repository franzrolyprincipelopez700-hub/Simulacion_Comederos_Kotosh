# Modelo 1.0.0: jornada finita

## Frontera y unidades

La frontera contiene **reserva y comederos**. Masa en kg, reloj en minutos, demanda potencial del lote en kg/h, tiempo de atención en minutos-persona. Una recarga mueve masa dentro de la frontera. La pérdida de entrega sale de la reserva durante esa transferencia; no es consumo. Remanentes accesibles y reserva final son alimento utilizable, no desperdicio. No se implementan retiros físicos en la primera versión; el término de retiros recuperables vale cero y figura explícitamente en el balance.

`inicial = reserva inicial + suma de masas iniciales de comederos`.

`inicial + entradas externas = consumo + pérdidas + retiros recuperables + final`.

`final = reserva final + suma de masas finales de comederos`.

Tolerancia absoluta **1e-8 kg**. Los valores usan double precision. Un balance inconsistente hace fallar el trabajo; no se incorpora al análisis definitivo. También se prueban límites de cada comedero.

## Demanda y paso temporal

En cada paso de tamaño `step` (1 min inicial) se genera una demanda **puntual al inicio** para el intervalo siguiente: tasa × minutos dentro del servicio / 60 × multiplicador del perfil × factor aleatorio. El perfil divide el horizonte en tramos de igual duración; sus números son multiplicadores relativos de la tasa, no masas ni porcentajes. Los pesos positivos de los comederos se normalizan para distribuir la demanda. No hay un segundo proceso de consumo.

Se consume como máximo el stock accesible. Con obstrucción, el consumo de ese comedero es cero. Si se habilita redistribución, la demanda que no se pudo atender se intenta una vez en otros comederos, proporcionalmente a sus existencias accesibles. Lo que sigue sin atender queda registrado y **no se acumula**. La demanda total permanece igual. El consumo de un comedero puede superar su cuota original porque atiende aves redistribuidas; las cuotas de demanda potencial y demanda no atendida se atribuyen proporcionalmente al reparto original, mientras el consumo individual refleja masa físicamente retirada.

Para cada intervalo se cuenta sin acceso si, después del consumo puntual, el comedero está vacío u obstruido. Se integra solo la intersección con la ventana de servicio. El OR evita duplicar vacío + obstrucción. Los periodos adyacentes se unen. Esta es una aproximación temporal deliberada: una recarga o reparación dentro del intervalo puede no reflejarse hasta el siguiente paso. No representa consumo continuo exacto. Tampoco debe cambiarse `step` en un experimento emparejado de políticas; se evalúa en sensibilidad separada.

Comprobación determinista con valores iniciales, políticas P0/P1/P2 y pasos 2, 1, 0,5 y 0,25 min: P0 y P1 conservaron 5,3333 min/comedero; P2 dio 19,3333, 17,0000, 16,5000 y 16,2500 respectivamente. El consumo fue 5,76 kg y las recargas/trabajo quedaron iguales. El paso de 1 min **no se declara universalmente convergido**: diferencias pequeñas requieren reducirlo y estudiar decisiones cercanas al umbral. Ejecutar `scripts/resolution.py` reproduce la comprobación.

## Servicio, recurso y políticas

Una persona usa un `simpy.Resource(capacity=1)`. No pueden coincidir inspección, desplazamiento, preparación, carga ni reparación. Cada inspección es una ronda compartida contada una sola vez, detecta al terminar y genera solicitudes sin duplicar una necesidad pendiente. No hay sensores.

- **P0:** horarios configurables, objetivo, máximo de kg añadidos y demora. Etiqueta referencia sintética mientras no exista operación observada.
- **P1:** rondas programadas desde el minuto cero cada `interval`, solicitudes si falta masa para el objetivo.
- **P2:** rondas cada `interval`, solicitud si nivel ≤ umbral de capacidad al completar la inspección. No detecta inmediatamente un cruce. La opción hipotética `continuous` programa rondas cada `step`, conserva su duración y competencia por la persona; por ello es observación de alta frecuencia, no detección matemática instantánea.

La demora P0 es espera pasiva antes de que una solicitud sea elegible para entrar al recurso. **FIFO entre tareas elegibles**; una incidencia inmediata puede adelantarse a una solicitud aún en demora. Las solicitudes ya elegibles siguen el orden de llegada, sin prioridad por comedero. Las rondas atrasadas esperan el recurso y se realizan cuando esté libre; no se atienden simultáneamente.

La atención empieza después de conseguir la persona. Termina tras desplazamiento + preparación + carga (o reparación). El alimento se incorpora **al terminar**, recalculando espacio y stock. Si `l` es la fracción perdida y `s` el espacio al objetivo, se retira `min(reserva, s/(1-l))`; se añade retirada × `(1-l)`. P0 restringe además `s` por su cantidad máxima. No hay capacidades excedidas ni reserva negativa.

Con reserva agotada una visita termina sin recarga positiva, libera la solicitud y registra `sin_reserva`; la siguiente ronda puede volver a solicitar. Las rondas tienen intervalo estrictamente positivo. Las entradas externas reponen reserva en momentos explícitos; no activan atención instantánea. Al cerrar permanecen pendientes las solicitudes sin completar.

Una incidencia preparada bloquea el acceso, conserva stock y se considera visible inmediatamente. Su reparación compite por la persona. Si comienza durante una recarga, se conserva el bloqueo y se solicita reparación al finalizar. Incidencias adicionales en un comedero ya bloqueado se agrupan en la misma necesidad. No se simula diagnóstico probabilístico ni sensores físicos.

## Variabilidad y emparejamiento

Modo determinista: factores iguales a 1. Modo variable: uniformes acotadas en `[1-variation, 1+variation]` para demanda y duración activa; inicial ±20 %. No produce masas o duraciones negativas. Tiempos nominales de inspección/carga etc. se multiplican por un factor indexado por `(paso de inicio, comedero, tipo de actividad)`.

Flujos distintos: demanda, atención e incidencias, identificadores iniciales 11, 22, 33. Cada réplica usa `SeedSequence([semilla, índice de réplica, identificador de flujo])`. La demanda exógena y candidatos de incidencia se pregeneran por tiempo, y la atención usa una malla por tiempo/actividad, evitando que las políticas desplacen una secuencia al solicitar diferente cantidad de atenciones. La malla alinea factores cuando coinciden tiempo y actividad; actividades iniciadas en instantes diferentes no tienen necesariamente el mismo factor. Esto permite números aleatorios comunes para entradas exógenas, no promete igualdad de tareas inducidas por políticas.

La incidencia aleatoria opcional usa probabilidad horaria `random_incidence_probability`, aproximada por una Bernoulli por paso con p = valor × step/60. No es un proceso Poisson exacto. Los eventos preparados siguen presentes si no se retiran explícitamente del escenario.

Cada llamada crea entorno, reserva, persona, series y flujos nuevos. Réplicas distintas son bloques independientes. Políticas dentro del mismo bloque comparten condiciones exógenas, semilla y resolución. La API rechaza condiciones externas diferentes en una comparación emparejada. Sensibilidad permite cambiar entradas y se analiza descriptivamente.

## Eventos simultáneos y cierre

SimPy ordena por tiempo, prioridad interna y orden FIFO de inserción para empates. Se registran inicialmente procesos de entradas externas, incidencias preparadas, inspecciones y demanda, en ese orden. En pasos posteriores el orden deriva de la inserción de sus timeouts; no se aplica una prioridad artificial diferente. La convención es reproducible y común a las políticas. Consultar eventos preserva su orden.

Horizonte **[0,H)**: `env.run(until=H)` excluye eventos de finalización exactamente en H. Disponibilidad del responsable **[inicio,fin)**: una tarea que termina en su instante de fin no añade alimento. El trabajo activo se trunca al horizonte o fin de disponibilidad, pero la atención no completada conserva su solicitud. La ventana de servicio limita demanda e interrupciones. No se borra calentamiento: es una jornada finita.

## Indicadores por réplica de sistema

1. Tiempo medio sin alimento: suma de minutos sin acceso / comederos. Unidad min/comedero.
2. Desperdicio: 100 × pérdidas / (masa inicial + entradas externas). Si denominador cero: no calculable. Incluye reserva y pérdidas de carga, sin contar recargas como entradas.
3. Recargas: incorporaciones positivas completadas antes de H. Inspecciones, visitas y solicitudes tienen contadores separados.
4. Trabajo: suma de duración activa efectivamente dentro del horizonte y disponibilidad; excluye espera y demora pasiva. La ronda compartida se cuenta una vez.
5. Disponibilidad: 100 × (1 - suma de minutos sin acceso / suma de minutos requeridos); acotada a [0,100].

## Inferencia y decisiones

Cada unidad experimental es una **jornada del sistema**, no un comedero. Medias y DE se calculan entre réplicas con varianza muestral. IC bilateral: media ± t(1-alpha/2,n-1) × DE/√n. Con n=1 no se informa IC.

Para cada alternativa vs P0 se calcula primero la diferencia dentro de cada bloque completo; IC y t de una muestra sobre esas diferencias. Desabastecimiento: H1 diferencia < 0. Desperdicio, recargas y trabajo: bilaterales. Alfa inicial 0,05. Familias previstas: un indicador, todas las alternativas contra P0. Holm conserva el tamaño previsto; pruebas no calculables equivalen a p=1 para ajustar las otras y mantienen p/valor ajustado como no calculable. Si no hay variabilidad de diferencias, el contraste t es degenerado: se informa la diferencia descriptiva, **no se inventa una p**.

Supuestos: independencia entre jornadas y aproximación razonable de medias/diferencias para inferencia t. 30 réplicas es un piloto editable, no garantía de precisión. Los resultados son exploratorios salvo bloque marcado de confirmación; el botón de confirmación usa semilla +100000. Para una confirmación formal fija previamente familia, límites y tamaño, conservando identificación del piloto. No se implementa cálculo automático de potencia.

Sin ambos límites (pérdida % y trabajo min-persona), no se recomienda ganadora. Con límites, se comprueban cotas superiores de IC y se ordenan alternativas factibles por continuidad, conservando los demás indicadores. Esta es una ayuda descriptiva para decisión; no certifica superioridad estadística. Si P0 ya tiene cero tiempo sin alimento se declara que no puede reducirse por debajo de cero. No se suma un puntaje de unidades distintas.

## Supuestos sintéticos iniciales

Tres comederos: 1,5 kg efectivos, 1 kg inicial, igual peso de demanda. 120 aves sin crecimiento biológico. 480 minutos de jornada/servicio/disponibilidad. 0,72 kg/h para el lote; perfil constante. Reserva 8 kg; sin entradas externas. Inspección 2 min compartidos; desplazamiento 2, preparación 2 y carga 3 min por atención; reparación 12 min. Pérdida 2 % de masa retirada de reserva en carga. Aves pueden redistribuirse. Incidencia C2 minuto 210. P0 horarios 120 y 300, demora 10 min, máximo añadido 1 kg. P1 intervalo inicial 120 min. P2 umbral 30 %, inspección inicial 120 min. Objetivo 100 %. Semilla 2026. Todos son **supuestos de demostración**, modificables y pendientes de medición. Campos `provenance` y `limits_origin` conservan la procedencia declarada por el usuario.
