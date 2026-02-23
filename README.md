# Censo Empresas - TFM

Trabajo Fin de Máster – Máster en Desarrollo con Inteligencia Artificial  

Autor: [Oskar Ollakarizketa Pérez]  
Repositorio: https://github.com/Iponichi/censoempresas  

---

## 1. Descripción del Proyecto

Aplicación web interna desarrollada en Python con Streamlit para la consulta de un Censo de Empresas almacenado en Microsoft SQL Server.

La aplicación permite:

- Consultar empresas por provincia y población
- Filtrar empresas activas según una fecha de referencia
- Aplicar la regla de negocio obligatoria basada en fechas históricas
- Exportar los resultados a CSV
- Cambiar entre entorno real y entorno demo mediante configuración

El objetivo del proyecto es construir una solución sencilla, funcional y mantenible que cumpla los requisitos académicos del TFM.

---

## 2. Arquitectura

La aplicación sigue una arquitectura simple en dos capas:

### 🔹 Capa de Presentación
- `app.py`
- Interfaz construida exclusivamente con Streamlit
- Gestión de filtros y visualización de resultados

### 🔹 Capa de Acceso a Datos
- `data_access.py`
- Conexión a SQL Server mediante SQLAlchemy + pyodbc
- Consultas parametrizadas (seguras)
- Aplicación de la lógica de negocio

Separación clara entre UI y acceso a datos.

---

## 3. Tecnologías Utilizadas

- Python 3.12
- Streamlit
- SQLAlchemy
- pyodbc
- Microsoft SQL Server
- Git + GitHub

No se utilizan tecnologías frontend externas (HTML/JS/React).

---

## 4. Modelo de Datos

### Tabla CENSO1
Contiene un registro por empresa (dirección fiscal).

Campos relevantes:
- DNI (NIF)
- NOMBRE
- PROVINCIA
- POBLACION

### Tabla CENSO2
Contiene los epígrafes históricos de cada empresa.

Campos relevantes:
- DNI (NIF)
- EPIGRAFE
- F_INI
- F_FIN

Relación:
- CENSO1.dni = CENSO2.dni


---

## 5. Lógica de Negocio (Obligatoria)

Una empresa se considera **activa** en una fecha determinada si existe al menos un epígrafe en CENSO2 que cumpla: 
- F_INICIO <= reference_date AND F_FIN > reference_date

Si no existe ninguno → empresa inactiva.

Esta lógica se implementa mediante cláusula `EXISTS` en SQL.

---

## 6. Funcionalidades del MVP

✔ Filtro por provincia  
✔ Filtro por población  
✔ Checkbox "Solo empresas activas"  
✔ Selector de fecha de referencia  
✔ Consulta SQL parametrizada  
✔ Exportación a CSV  
✔ Configuración por entorno (.env)  

---

## 7. Configuración del Entorno

Las credenciales NO están en el código.

Se utilizan variables de entorno mediante archivo `.env`.

Ejemplo (`.env.example`):

DB_MODE=real

DB_HOST=SERVER_NAME
DB_PORT=1433
DB_NAME=DATABASE_NAME
DB_USER=USERNAME
DB_PASSWORD=PASSWORD
DB_DRIVER=ODBC Driver 17 for SQL Server


El archivo `.env` real no se sube al repositorio.

---

## 8. Instalación y Ejecución

### 1. Clonar el repositorio
git clone https://github.com/Iponichi/censoempresas.git

cd censoempresas

### 2. Crear entorno virtual
py -3.12 -m venv .venv
..venv\Scripts\Activate.ps1

### 3. Instalar dependencias
pip install -r requirements.txt


### 4. Configurar archivo .env

Crear archivo `.env` con credenciales reales.

### 5. Ejecutar aplicación
streamlit run app.py

---

## 9. Seguridad

- No se almacenan credenciales en el código
- Uso de archivo `.env`
- Consultas SQL parametrizadas
- `.env` excluido mediante `.gitignore`

---

## 10. Control de Versiones

Repositorio público en GitHub.

Se han realizado commits frecuentes que reflejan la evolución del proyecto:

- Initial structure
- Database connection
- Streamlit integration
- Active business rule
- Real filters implementation

---

## 11. Mejoras Futuras

- Filtro por epígrafe
- Consultas por rango de fechas
- Visualización por epígrafes activos
- Integración opcional de lenguaje natural para generación de filtros

---

## 12. Conclusión

El proyecto demuestra:

- Conexión segura a SQL Server
- Aplicación de lógica de negocio histórica
- Desarrollo rápido con Streamlit
- Buenas prácticas de configuración y control de versiones
- Separación clara de responsabilidades

Aplicación sencilla, funcional y mantenible.
