# Censo Empresas - TFM

Trabajo Fin de Máster – Máster en Desarrollo con Inteligencia Artificial  

Autor: [Oskar Ollakarizketa Pérez]  
Repositorio: https://github.com/Iponichi/censoempresas  

---

## 1. Descripción del Proyecto

Aplicación web interna desarrollada en Python con Streamlit para la consulta de un Censo de Empresas almacenado en Microsoft SQL Server.

La aplicación permite:

- Consultar empresas por provincia y localidad
- Filtrar empresas activas según una fecha de referencia
- Filtrar por epígrafe de actividad
- Aplicar una regla de negocio obligatoria basada en fechas históricas
- Exportar los resultados a CSV
- Cambiar entre entorno real y entorno demo mediante configuración

El objetivo del proyecto es construir una solución sencilla, funcional y mantenible que cumpla los requisitos académicos del TFM, priorizando claridad estructural y buenas prácticas de desarrollo.
---

## 2. Arquitectura

La aplicación sigue una arquitectura en dos capas claramente separadas.

### 🔹 Capa de Presentación
- `app.py`
Responsabilidades:
- Construcción de la interfaz con Streamlit
- Gestión de filtros
- Visualización de resultados
- Exportación de datos a CSV
- Interacción con el usuario
No contiene lógica SQL ni credenciales.

### 🔹 Capa de Acceso a Datos
- `data_access.py`
Responsabilidades:
- Carga de configuración desde archivo .env
- Creación del engine SQLAlchemy
- Ejecución de consultas parametrizadas
- Aplicación de la lógica de negocio
- Obtención dinámica de valores para filtros
Se utiliza SQLAlchemy junto con pyodbc para la conexión a SQL Server.

---

## 3. Tecnologías Utilizadas

- Python 3.12
- Streamlit
- SQLAlchemy
- pyodbc
- Microsoft SQL Server
- Git + GitHub
No se emplean tecnologías frontend externas (HTML, JavaScript o frameworks SPA).
Toda la aplicación está desarrollada íntegramente en Python.

---

## 4. Modelo de Datos

### Tabla CENSO1
Contiene un registro por empresa (dirección fiscal).

Campos relevantes:
- DNI (NIF)
- NOMBRE
- PROVINCIA
- LOCALIDAD

### Tabla CENSO2
Contiene los epígrafes históricos de cada empresa.

Campos relevantes:
- DNI (NIF)
- EPIGRAFE
- F_INICIO
- F_FIN

Relación entre tablas:
Relación uno a muchos:
- CENSO1.dni = CENSO2.dni
Una empresa puede tener múltiples registros en CENSO2 si:
    Tiene varios epígrafes
    Ha cambiado de actividad en el tiempo
    Tiene periodos históricos distintos
---

## 5. Lógica de Negocio (Obligatoria)

Una empresa se considera activa en una fecha determinada si existe al menos un registro en CENSO2 que cumpla:
- F_INICIO <= reference_date AND F_FIN > reference_date

Si no existe ningún registro que cumpla esa condición, la empresa se considera inactiva.

Esta lógica se implementa mediante cláusula EXISTS en SQL, garantizando eficiencia y correcta aplicación de la regla histórica.
---

## 6. Funcionalidades del MVP

- Filtro por provincia (valores cargados dinámicamente desde la base de datos)
-  Filtro por localidad dependiente de la provincia seleccionada
-  Filtro por epígrafe
-  Checkbox "Solo empresas activas"
-  Selector de fecha de referencia
-  Aplicación de la regla histórica obligatoria
-  Consulta SQL parametrizada
-  Exportación de resultados a CSV
-  Configuración por entorno mediante .env
-  Separación clara entre presentación y acceso a dato

---

## 7. Configuración del Entorno

Las credenciales NO están en el código.
Se utilizan variables de entorno mediante archivo `.env`.
Ejemplo (`.env.example`):

- DB_MODE=real

- DB_HOST=SERVER_NAME
- DB_PORT=1433
- DB_NAME=DATABASE_NAME
- DB_USER=USERNAME
- DB_PASSWORD=PASSWORD
- DB_DRIVER=ODBC Driver 17 for SQL Server


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

- No se almacenan credenciales en el repositorio
- Uso obligatorio de variables de entorno
- Consultas SQL parametrizadas
- Separación de responsabilidades
- Archivo .env excluido mediante .gitignore

---

## 10. Control de Versiones

Repositorio público en GitHub.

Se han realizado commits frecuentes que reflejan la evolución del proyecto:

- Estructura inicial

- Conexión a base de datos
- Integración con Streamlit
- Implementación de la regla de negocio
- Filtros dinámicos desde base de datos
- Integración de filtro por epígrafe
---

## 11. Mejoras Futuras

- Filtro por epígrafe
- Consultas por rango de fechas
- Visualización por epígrafes activos
- Integración opcional de lenguaje natural para generación de filtros

---

## 12. Conclusión

El proyecto demuestra:
- Conexión segura a Microsoft SQL Server
- Implementación correcta de lógica histórica de negocio
- Arquitectura limpia en dos capas
- Uso de consultas parametrizadas
- Aplicación de buenas prácticas de configuración y versionado

Se trata de una aplicación sencilla, funcional y mantenible, adecuada al alcance académico del Trabajo Fin de Máster.


