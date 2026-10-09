import React,{useId,useState} from 'react';
import {CircleHelp} from 'lucide-react';

const guides:Record<string,string>={
 'Nombre del escenario':'Escribe un nombre que te permita reconocer esta configuración. Ejemplo: “Lote A · turno de mañana”. Guardar una edición crea una nueva versión.',
 'Número de aves':'Ingresa cuántas aves utilizan estos comederos durante la jornada. Ejemplo: 120. La demanda de alimento se ingresa para todo ese lote, no por ave.',
 'Características del lote':'Describe edad, tipo de ave y etapa productiva. Ejemplo: “120 pollos de engorde, 4 semanas”. Esta descripción sirve para identificar y comparar lotes.',
 'Identificación':'Usa un código distinto para cada comedero, como C1, C2 o C3. Ese mismo código aparecerá en gráficos, eventos y datos de campo.',
 'Capacidad efectiva':'Indica los kg que realmente puede contener el comedero sin desbordarse. Ejemplo: 1,5 kg. Usa la capacidad útil, no el tamaño del envase de alimento.',
 'Alimento inicial':'Escribe cuántos kg hay en este comedero al comenzar. Ejemplo: 1 kg en un comedero de 1,5 kg. No puede superar su capacidad.',
 'Peso de demanda':'Indica qué parte del lote utiliza este comedero, en relación con los demás. Usa 1 en todos para reparto igual. Pesos 2, 1, 1 reparten 50 %, 25 % y 25 % de la demanda.',
 'Duración de jornada':'Ingresa la duración total en minutos. Ejemplo: 8 horas = 480 minutos. Las ventanas de alimento y del responsable deben terminar dentro de ese tiempo.',
 'Inicio del servicio requerido':'Minuto desde el que las aves necesitan alimento. Usa 0 si lo necesitan desde el inicio de la jornada. Si empiezan una hora después, escribe 60.',
 'Fin del servicio requerido':'Minuto hasta el que las aves necesitan alimento. En una jornada de 8 horas escribe 480. Debe ser mayor que el inicio y no superar la duración.',
 'Demanda potencial del lote':'Ingresa los kg que requiere todo el lote por hora. Si esperas 5,76 kg en 8 horas: 5,76 ÷ 8 = 0,72 kg/h. No ingreses aquí el consumo de una sola ave.',
 'Reserva inicial':'Alimento que el responsable tiene listo para recargar, fuera de los comederos. Ejemplo: 8 kg. No sumes el alimento inicial de los comederos: se registra por separado.',
 'Disponible desde':'Minuto en que el responsable empieza a poder atender. Escribe 0 si está desde el inicio, o 60 si llega una hora después.',
 'Disponible hasta':'Minuto en que termina la disponibilidad del responsable. Ejemplo: 480 para una jornada de 8 horas. Después no se completan nuevas atenciones.',
 'Inspección compartida':'Minutos para revisar todos los comederos en una ronda. Ejemplo: 2 minutos en total. No ingreses el tiempo por comedero; la ronda se cuenta una vez.',
 'Desplazamiento':'Minutos para ir hasta el comedero que necesita atención. Ejemplo: 2 minutos por visita. No incluyas preparación ni carga.',
 'Preparación':'Minutos para preparar alimento y herramientas antes de cargar o resolver la incidencia. Ejemplo: 2 minutos. Se suman al desplazamiento y a la tarea.',
 'Carga':'Minutos para incorporar alimento en un comedero. Ejemplo: 3 minutos. La nueva masa se incorpora al terminar esta tarea, no al solicitarla.',
 'Resolver obstrucción':'Minutos necesarios para despejar un comedero y permitir acceso al alimento. Ejemplo: 12 minutos, además de desplazamiento y preparación.',
 'Pérdida durante la carga':'Porcentaje del alimento retirado de la reserva que se pierde al cargar. Escribe 2 para una pérdida de 2 %. Escribe 0 si no hay pérdidas.',
 'Objetivo de llenado':'Porcentaje de capacidad al que quieres llegar en cada recarga. Ejemplo: 80 llena hasta 1,2 kg un comedero de 1,5 kg. Usa 100 para llenarlo completamente.',
 'Intervalo entre inspecciones':'Minutos entre rondas para revisar el nivel. Ejemplo: 30 significa una ronda cada media hora. Un nivel bajo se detecta al terminar la inspección.',
 'Intervalo de reposición':'Minutos entre rondas programadas de reposición. Ejemplo: 90 equivale a una ronda cada hora y media. Las solicitudes esperan si el responsable está ocupado.',
 'Umbral mínimo':'Porcentaje de capacidad que activa una solicitud cuando se inspecciona. Ejemplo: 20 equivale a 0,3 kg en un comedero de 1,5 kg. Debe ser menor que el objetivo.',
 'Horarios de referencia':'Escribe minutos desde el inicio, separados por comas. Ejemplo: 120, 300 programa rondas a las 2 y a las 5 horas. No uses horas del reloj como 08:00.',
 'Cantidad máxima por recarga':'Máximo de kg que se añadirán en una recarga de referencia. Ejemplo: 1 kg. El motor limita además por capacidad, objetivo y reserva disponible.',
 'Demora de referencia':'Minutos de espera antes de que una solicitud de referencia entre a la cola de atención. Ejemplo: 10. No se cuentan como trabajo activo.',
 'Réplicas por alternativa':'Número de jornadas que se calcularán con cada opción. Ejemplo: 30 permite ver variabilidad. Más réplicas requieren más cálculo; una sola no estima un intervalo de confianza.',
 'Semilla del nuevo bloque':'Número entero para reproducir el experimento. El mismo número y la misma configuración generan el mismo resultado. Para un bloque nuevo usa otro número, por ejemplo 102026.',
 'Intervalos P1':'Escribe hasta dos intervalos en minutos, separados por comas. Ejemplo: 90, 150. Se comparará una ronda cada 90 minutos y otra cada 150.',
 'Objetivos de llenado':'Escribe hasta dos porcentajes, separados por comas. Ejemplo: 80, 100. Se probará llenar al 80 % y al 100 % de la capacidad.',
 'Umbrales P2':'Escribe hasta dos porcentajes de capacidad. Ejemplo: 20, 35. Se solicitará recarga al detectar un nivel igual o inferior a cada umbral.',
 'Intervalos de inspección P2':'Escribe hasta dos intervalos en minutos. Ejemplo: 30, 60. Se compararán revisiones cada media hora y cada hora.',
 'Máximo desperdicio aceptable':'Porcentaje máximo de pérdida que aceptarías. Ejemplo: 2 %. Déjalo vacío si aún no definiste un límite. Se usa para filtrar alternativas, no para cambiar sus resultados.',
 'Máximo trabajo aceptable':'Máximos minutos activos del responsable durante toda la jornada. Ejemplo: 90 minutos-persona. No ingreses las 8 horas del turno si parte de ese tiempo realiza otras tareas.',
 'Procedencia de límites':'Indica de dónde sale tu límite. Ejemplo: “El responsable puede dedicar 90 minutos por jornada; acuerdo del 08/10”. Así la decisión puede revisarse después.',
 'Entrada que se modifica':'Selecciona qué quieres explorar: consumo del lote, reserva, tiempo de carga o paso temporal. Las demás condiciones se mantienen para observar el efecto de esa entrada.',
 'Valores del rango':'Escribe los valores de la entrada elegida, separados por comas y en su unidad. Para demanda: 0.5, 0.72, 1 kg/h. Para reserva: 4, 8, 12 kg.',
 'Procedencia general':'Selecciona “Dato medido” para registros del lote, “Fuente externa” para bibliografía o “Supuesto de demostración” para ejemplos. Puedes detallar cada parámetro en opciones avanzadas.',
 'Modo de simulación':'“Sin variabilidad” mantiene tiempos y demanda constantes. “Con variabilidad” permite diferencias entre jornadas, usando la variación configurada en opciones avanzadas.',
 'Nombre del conjunto':'Nombre para identificar las observaciones. Ejemplo: “Lote A · octubre · calibración”. Usa un conjunto distinto para las jornadas reservadas de validación.',
 'Origen':'Elige observado para registros recogidos en campo o sintético para ejemplos preparados. La selección se conserva junto con las observaciones.',
 'Uso de jornadas completas':'Calibración: jornadas para ajustar parámetros. Validación reservada: jornadas distintas para comprobar resultados después del ajuste.',
 'Añadir a conjunto existente':'Selecciona un conjunto para añadir filas y detectar duplicados contra sus registros. Deja “Crear conjunto nuevo” si es tu primera importación.',
 'Experimento de referencia':'Selecciona un experimento completado que incluya P0. Sus promedios se comparan con los indicadores calculados de las jornadas reservadas.',
 'Datos observados de validación':'Selecciona jornadas de campo reservadas para validación. Deben corresponder a condiciones comparables: lote, duración, comederos y frontera del alimento.',
 'Fecha':'Fecha de la jornada observada. Usa el calendario o escribe AAAA-MM-DD. Ejemplo: 2026-10-08.',
 'Inicio / hora':'Hora en que ocurrió el evento o comenzó la actividad. Ejemplo: 08:15. Para una actividad o interrupción añade también la hora de fin.',
 'Comedero (SISTEMA para tarea compartida)':'Usa el mismo código de tu configuración, por ejemplo C1. Escribe SISTEMA para una actividad compartida del responsable o una cantidad de toda la unidad.',
 'Cantidad (kg)':'Masa medida en kg para este registro. Ejemplo: 0,5 kg suministrados o remanentes. No uses gramos sin convertirlos: 500 g = 0,5 kg.',
 'Fin (para actividad o interrupción)':'Hora en que terminó la actividad o se recuperó el acceso. Debe ser posterior al inicio, dentro del mismo día. Para una recarga puntual puede quedar vacío.',
 'Notas':'Detalle que permita interpretar la observación. Ejemplo: “Obstrucción por alimento compactado” o “Carga medida con balanza”.',
 'Tipo':'Elige qué registraste: suministro, consumo, remanente, pérdida, inspección, recarga, actividad o interrupción. Actividades e interrupciones necesitan inicio y fin.',
 'Jornadas para calibración':'Cantidad de días completos que planeas observar para ajustar parámetros. Ejemplo: 10. Es una meta de recolección, no el número de días ya registrados.',
 'Jornadas reservadas para validación':'Cantidad de días distintos que reservarás para contrastar el modelo después de calibrarlo. Ejemplo: 5. No reutilices las mismas fechas de calibración.',
 'Límite de desperdicio':'Porcentaje máximo de pérdida que aceptas para esta revisión. Ejemplo: 2. El filtro conserva alternativas dentro de ese límite.',
 'Límite de trabajo':'Minutos activos disponibles para abastecimiento en toda la jornada. Ejemplo: 90. El filtro descarta opciones que exijan más trabajo.',
 'Si hay igual continuidad, priorizar':'Cuando varias opciones tienen el mismo tiempo sin alimento, elige qué te interesa reducir primero: minutos de trabajo o porcentaje de pérdida. Solo se consideran opciones que cumplen los dos límites.',
};
export function guidance(label:string,help?:string,unit?:string){
 if(guides[label])return guides[label];
 if(label.startsWith('Tolerancia:'))return `Diferencia absoluta máxima que aceptarás entre el promedio observado y el calculado para ${label.slice(11).toLowerCase()}. Usa ${unit||'la unidad del indicador'}. Por ejemplo: tolerancia 10 en tiempo permite una diferencia de hasta 10 min/comedero.`;
 return help||`Ingresa ${label.toLowerCase()}${unit?' en '+unit:''}. Usa el valor correspondiente a la jornada o lote que estás configurando.`;
}
export function HelpTip({label,help,unit}: {label:string,help?:string,unit?:string}){
 const [hover,setHover]=useState(false),[pinned,setPinned]=useState(false),[position,setPosition]=useState<React.CSSProperties>({});const id=useId();const open=hover||pinned;
 function place(el:HTMLElement){const r=el.getBoundingClientRect(),width=Math.min(310,window.innerWidth-32);setPosition({position:'fixed',width,left:Math.max(16,Math.min(r.left-35,window.innerWidth-width-16)),...(r.bottom>window.innerHeight-240?{top:'auto',bottom:window.innerHeight-r.top+7}:{top:r.bottom+7,bottom:'auto'})})}
 return <span className="help-anchor" onMouseEnter={e=>{place(e.currentTarget);setHover(true)}} onMouseLeave={()=>setHover(false)}><button type="button" className={'help-trigger '+(pinned?'pinned':'')} aria-label={'Ayuda: '+label} aria-expanded={open} aria-describedby={open?id:undefined} onFocus={e=>{place(e.currentTarget);setHover(true)}} onBlur={()=>setHover(false)} onClick={e=>{e.preventDefault();place(e.currentTarget);setPinned(!pinned)}} onKeyDown={e=>{if(e.key==='Escape'){setPinned(false);setHover(false)}}}><CircleHelp size={16}/></button>{open&&<span id={id} role="tooltip" className="help-popover" style={position}><strong>{label}</strong><span>{guidance(label,help,unit)}</span><small>{pinned?'Clic en ? o Esc para cerrar':'Puedes hacer clic para mantener la ayuda abierta.'}</small></span>}</span>
}
export function Field({label,value,onChange,unit,type='number',min,max,step='any',help,required=true}:any){
 const id=useId();return <div className="field"><div className="field-label"><label htmlFor={id}>{label}</label><HelpTip label={label} help={help} unit={unit}/>{unit&&<small>{unit}</small>}</div><input id={id} type={type} value={value??''} min={min} max={max} step={step} required={required} onChange={e=>onChange(type==='number'?(e.target.value===''?'':Number(e.target.value)):e.target.value)}/></div>
}
export function SelectField({label,children}:any){const id=useId();return <div className="field"><div className="field-label"><label htmlFor={id}>{label}</label><HelpTip label={label}/></div>{React.cloneElement(children,{id})}</div>}
