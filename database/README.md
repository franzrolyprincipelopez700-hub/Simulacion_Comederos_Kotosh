# Copia PostgreSQL incluida

`simulador_avicola.backup` contiene el esquema y los datos de la aplicación al momento de la exportación. Es un archivo custom producido con `pg_dump` 18, sin roles, propietarios ni permisos del servidor original. No incluye `backend/.env` ni la contraseña PostgreSQL.

`simulador_avicola.manifest.json` registra fecha UTC, versión del modelo, revisión Alembic, tamaño, SHA-256 y conteos por tabla. La copia actual contiene escenarios y experimentos de ejemplo; no hay conjuntos de observaciones de campo. La reserva y las demás entradas pertenecen a las configuraciones de los experimentos.

La copia es una instantánea: los experimentos que ejecutes después no cambian este archivo. Usa una base PostgreSQL 18 nueva y vacía, configurada con tus propias credenciales en `backend/.env`:

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\restore_database.py
powershell -ExecutionPolicy Bypass -File .\scripts\migrate.ps1
```

Consulta [LEEME_INSTALACION.txt](../LEEME_INSTALACION.txt) para descargar, instalar dependencias, configurar la conexión y arrancar. El script se niega a sobrescribir una base con objetos y comprueba el archivo y los conteos.
