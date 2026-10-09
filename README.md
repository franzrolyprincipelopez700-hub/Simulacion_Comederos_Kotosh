# Simulador Avícola Kotosh

Aplicación web **local** para el proyecto “Desarrollo de un modelo de simulación para mejorar el abastecimiento de alimento en comederos avícolas de Kotosh, Huánuco, 2026”. Motor real SimPy, FastAPI, PostgreSQL y React. Los datos incluidos son **sintéticos**, no mediciones de Kotosh. No requiere sensores, servicios de pago ni internet para calcular jornadas después de instalar las dependencias.

## Descargar e instalar en otra computadora

Repositorio: [Simulacion_Comederos_Kotosh](https://github.com/franzrolyprincipelopez700-hub/Simulacion_Comederos_Kotosh). Puedes usar **Code → Download ZIP** y extraer todo, o clonar:

```powershell
git clone https://github.com/franzrolyprincipelopez700-hub/Simulacion_Comederos_Kotosh.git
cd Simulacion_Comederos_Kotosh
```

La guía completa, con requisitos, configuración, restauración y soluciones a errores, está en **[LEEME_INSTALACION.txt](LEEME_INSTALACION.txt)**. Todas las instrucciones se ejecutan desde la carpeta descargada; no dependen de la ruta ni del usuario de la computadora original.

Requisitos probados: **Windows / PowerShell, Python 3.10, Node.js 24 con npm y PostgreSQL 18**. Instala el servidor PostgreSQL y sus herramientas de consola. pgAdmin es opcional; Chrome se utiliza únicamente para las pruebas del navegador. Necesitas internet para descargar dependencias; después la aplicación calcula localmente.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
notepad .\backend\.env
```

Configura tu usuario, contraseña, puerto y base. El script copia `.env.example`; debes reemplazar `YOUR_PASSWORD` por **tu contraseña local**, codificando los caracteres especiales como componente URL:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/simulador_avicola
```

### Opción A: incluir el historial entregado

La carpeta **[database](database/README.md)** incluye una copia PostgreSQL con esquema, escenarios y resultados guardados, junto con un inventario y SHA-256. No incluye usuarios ni contraseñas del servidor original. Configura una base **nueva y vacía** y ejecuta:

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\restore_database.py
powershell -ExecutionPolicy Bypass -File .\scripts\migrate.ps1
```

La restauración se niega a sobrescribir objetos existentes y comprueba los conteos. Si no encuentra `pg_restore`, configura `$env:POSTGRES_BIN = 'C:\Program Files\PostgreSQL\18\bin'` en esa ventana.

### Opción B: empezar sin historial

Ejecuta solamente `powershell -ExecutionPolicy Bypass -File .\scripts\migrate.ps1`. Crea la base si falta, aplica el esquema y conserva un escenario de demostración. **Elige A o B**: no inicialices el esquema antes de restaurar A.

El usuario PostgreSQL necesita permiso de creación de bases; si no lo tiene, un administrador debe crear una base vacía de su propiedad. Los scripts respetan el nombre de base configurado en `.env`.

### Iniciar

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

Abre **http://127.0.0.1:5174/**. API: http://127.0.0.1:8000/docs. El arranque inicia API, trabajador separado y frontend. Para detener sus procesos: `powershell -ExecutionPolicy Bypass -File .\scripts\stop.ps1`. Los registros están en `backend/*.log` y `frontend/*.log`. Requiere puertos 8000 y 5174 libres y el servicio PostgreSQL activo.

Las dependencias resueltas están en `backend/requirements.lock.txt` y `frontend/package-lock.json`. No se incluyen `.venv`, `node_modules`, `.env` ni archivos temporales; se recrean en cada instalación.

## Demostración

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m app.seed
```

Carga idempotente, conserva información del usuario. En Inicio, **Abrir demostración** carga tres comederos de capacidad 1,5 kg, 1 kg inicial cada uno, lote de 120 aves, jornada de 480 minutos, demanda 0,72 kg/h, reserva 8 kg y obstrucción preparada de C2 al minuto 210. Todos son supuestos pendientes de verificación.

Revisa los pasos, guarda y ejecuta. Una ejecución individual usa una réplica. En **Comparar alternativas**, el piloto inicial propone 30 réplicas y la combinación P0 / 4 P1 / 8 P2. No garantiza precisión ni una política ganadora. Los límites operativos empiezan sin definir.

Ya hay un piloto calculado en el historial, denominado **Piloto sintético · 13 alternativas × 30 réplicas**. Sus 390 jornadas se calcularon y persistieron en 7,75 s; tiempo observado desde encolar hasta completar: 8,18 s (Windows, Python 3.10.8; consulta `docs/VERIFICACION.md`). Puedes reproducir la réplica 1 de cada alternativa y descargar resultados reales.

Para generar otro piloto y los archivos en `output/`, inicia API/trabajador y ejecuta desde la raíz:

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\pilot.py
```

## Funcionalidades

![Guía de uso del sistema](docs/images/guia-de-uso.png)

Los campos habituales incluyen ayudas `?` con instrucciones y ejemplos. Llenado, umbral y pérdida se ingresan en porcentajes. El panel de resultados incluye lectura operativa de cada jornada, comparación de continuidad/trabajo/pérdida, límites para filtrar opciones y elección de prioridad cuando hay igual continuidad. La guía de uso incluye propósito, recorrido de seis pasos, políticas, indicadores, criterios de decisión, datos de campo, preguntas frecuentes y glosario con búsqueda; los nuevos componentes están separados en `frontend/src/forms.tsx` y `frontend/src/decisions.tsx`.

- Inicio con conteos reales, últimos experimentos y guía.
- Configuración guiada, edición por versiones, duplicación y procedencia por parámetro en opciones avanzadas.
- P0 configurable por horarios/cantidad/demora, P1 periódica y P2 con detección por inspección.
- Una persona y cola FIFO; consumo, reservas, pérdidas y obstrucciones independientes; balance de masa comprobado.
- Reproducción de estados calculados con pausa, velocidad, reinicio, reloj, línea temporal, estados físicos y solicitudes separados.
- Indicadores por jornada y comedero, periodos de interrupción, actividades, balance y estado al cierre.
- Experimentos emparejados con medias, DE, IC t, contrastes direccionales/bilaterales y Holm; confirmación con nuevas semillas y sensibilidad descriptiva.
- Trabajador separado con cola PostgreSQL, bloqueo `SKIP LOCKED`, progreso, cancelación y recuperación por reintento completo.
- Historial persistente, búsqueda y paginación; detalle visual limitado a réplicas seleccionadas; CSV, Excel y PDF.
- Registro manual e importación CSV con vista previa, errores por fila, duplicados, separación de jornadas para calibración/validación y comparación de indicadores observados. Criterios y resultados de validación se conservan.

## Pruebas

Detén trabajadores mientras ejecutas las pruebas backend (las pruebas invocan su propio trabajador). Solo eliminan sus registros con prefijo reservado `TEST-`; nunca uses ese prefijo para datos personales.

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m alembic current
Set-Location ..\frontend
npm.cmd run build
npm.cmd audit
# Con API, trabajador y frontend iniciados; Chrome instalado
npm.cmd run test:e2e
```

Las pruebas Playwright usan Chrome en modo headless y generan capturas en `output/screenshots`. No necesitan instalar otro navegador. Las pruebas de interfaz generan resultados sintéticos reales. Detalle de comprobaciones y límites: [docs/VERIFICACION.md](docs/VERIFICACION.md).

## Estructura y futuras mejoras

| Archivo / carpeta | Responsabilidad |
|---|---|
| `backend/app/schemas.py` | Parámetros, validación y límites físicos |
| `backend/app/engine.py` | Procesos SimPy y estado de cada jornada |
| `backend/app/policies.py` | Calendario y detección de reposición |
| `backend/app/metrics.py` | Indicadores y conservación |
| `backend/app/analysis.py` | Estadística de bloques completos |
| `backend/app/db.py`, `backend/migrations/` | PostgreSQL, entidades, índices, Alembic |
| `backend/app/worker.py` | Cola, reclamación exclusiva y progreso |
| `backend/app/api.py` | API, persistencia e importación |
| `backend/app/field.py` | Observaciones y métricas de jornadas reservadas |
| `backend/app/exports.py` | Informes derivados de resultados guardados |
| `frontend/src/` | React/TypeScript, navegación, controles y gráficos |
| `backend/tests/`, `frontend/tests/` | Pruebas numéricas, integración y navegador |
| `scripts/` | Instalación, arranque, pruebas y piloto reproducible |

Para cambiar reglas o indicadores modifica su módulo y prueba sus invariantes; para nuevos parámetros amplía `schemas.py`, formulario y documentación. Los cambios de tablas requieren **una nueva migración**, no modificar migraciones aplicadas. Conserva las configuraciones y versión del modelo en las ejecuciones.

Más información: [modelo y supuestos](docs/MODELO.md), [guía operativa y presentación](docs/GUIA.md), [API y datos de campo](docs/API.md). Arquitectura y convenciones contrastadas con documentación primaria: [SimPy](https://simpy.readthedocs.io/en/stable/), [FastAPI](https://fastapi.tiangolo.com/), [Vite](https://vite.dev/guide/).

## Límites reales de esta versión

No hay mediciones reales ni validación de campo. La demanda se discretiza y puede cambiar el tiempo sin acceso y decisiones de umbral: usa sensibilidad de resolución. Las opciones menos frecuentes se editan como JSON validado en el panel avanzado. La importación de campo es CSV; Excel está implementado como **exportación de resultados**, no como importador. No se ajustan parámetros automáticamente a las observaciones: la calibración es manual y la comparación de validación es descriptiva contra criterios guardados. Un reintento comienza desde cero; no reanuda el reloj intermedio. La cancelación se aplica entre réplicas. No hay autenticación porque el alcance es un espacio local; no expongas los puertos a internet.
