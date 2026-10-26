# PRD — Global Threat Intelligence Platform

**Versión:** 1.0  
**Estado:** Borrador inicial para desarrollo  
**Tipo de proyecto:** Proyecto universitario de desarrollo de software y ciberseguridad  
**Categoría:** Cyber Threat Intelligence (CTI) / OSINT  
**Stack principal:** Python, FastAPI y PostgreSQL  
**Interfaz:** React + TypeScript  
**Idioma inicial:** Español  
**Plataforma objetivo:** Aplicación web  
**Duración estimada del MVP:** 6 semanas de desarrollo individual

----------

# 1. Resumen ejecutivo

Global Threat Intelligence Platform (GTIP) será una plataforma web que recopila y centraliza información pública sobre amenazas informáticas mediante la integración de múltiples APIs y fuentes de inteligencia de ciberseguridad.

Actualmente, la información sobre vulnerabilidades, indicadores maliciosos, direcciones IP sospechosas y URLs asociadas con malware se encuentra distribuida entre distintos proveedores. Consultar cada fuente por separado dificulta obtener una visión unificada de una amenaza.

GTIP busca resolver este problema mediante un sistema que obtenga datos de fuentes externas, los transforme a un formato común, los almacene en una base de datos propia y permita investigarlos desde una única interfaz.

La plataforma ofrecerá un dashboard general, un catálogo de vulnerabilidades, un buscador de indicadores de compromiso (IOC), un historial de observaciones y un módulo para supervisar el estado de las fuentes de información.

El proyecto tendrá una arquitectura modular que permita añadir nuevas fuentes sin modificar el funcionamiento general de la aplicación.

## 1.1. Propuesta de valor

Convertir información pública y dispersa sobre ciberseguridad en información centralizada, consultable y contextualizada, facilitando la investigación de amenazas informáticas.

## 1.2. Objetivo principal

Desarrollar una aplicación funcional capaz de consumir múltiples APIs públicas de ciberseguridad, procesar sus respuestas, persistir los datos y exponerlos mediante una API propia y una interfaz web.

## 1.3. Definición del producto

GTIP será una plataforma de inteligencia de amenazas externas con funciones de agregación, normalización, búsqueda y correlación de indicadores.

No se considerará un SIEM completo en su versión inicial, ya que no recopilará ni analizará de forma generalizada los registros internos de sistemas, servidores o dispositivos de red.

----------

# 2. Problema que resuelve

La información de ciberseguridad está distribuida entre diferentes servicios especializados.

Por ejemplo:

-   Un catálogo identifica vulnerabilidades que ya han sido explotadas.
    
-   Una base de datos proporciona detalles técnicos de vulnerabilidades conocidas.
    
-   Un servicio recopila URLs relacionadas con la distribución de malware.
    
-   Una plataforma de reputación recibe reportes sobre direcciones IP.
    
-   Una comunidad de inteligencia comparte indicadores y contexto sobre amenazas.
    

Un usuario que investiga un incidente puede necesitar consultar varias de estas fuentes, comparar resultados y registrar manualmente sus hallazgos.

GTIP centralizará ese proceso.

## 2.1. Problemas específicos

1.  Fragmentación de la información entre diferentes proveedores.
    
2.  Diferencias en los formatos y estructuras de las respuestas.
    
3.  Duplicación de indicadores reportados por múltiples fuentes.
    
4.  Dificultad para conservar el historial de observaciones.
    
5.  Falta de visibilidad sobre cuándo se actualizaron los datos.
    
6.  Dependencia de consultas manuales a diferentes servicios.
    

## 2.2. Solución propuesta

Construir un sistema que:

1.  Consulte automáticamente las fuentes configuradas.
    
2.  Valide y normalice sus respuestas.
    
3.  Guarde la información en PostgreSQL.
    
4.  Relacione los registros que correspondan al mismo indicador.
    
5.  Permita buscar y filtrar los datos desde una API y una interfaz web.
    
6.  Registre la procedencia, las fechas y los errores de cada proceso de ingesta.
    

----------

# 3. Usuarios objetivo

## 3.1. Estudiantes de ciberseguridad y TI

Necesitan investigar vulnerabilidades, indicadores y fuentes de inteligencia para aprender cómo funciona la identificación de amenazas.

## 3.2. Administradores de sistemas

Necesitan consultar información externa cuando encuentran direcciones IP, dominios o URLs sospechosas en sus sistemas.

## 3.3. Analistas de seguridad

Necesitan reunir contexto sobre indicadores durante una investigación y consultar evidencias procedentes de diferentes fuentes.

## 3.4. Equipos pequeños de TI

Pueden utilizar la plataforma como una herramienta complementaria para consultar vulnerabilidades y mantener una colección centralizada de inteligencia pública.

## 3.5. Usuario principal del MVP

El usuario principal será una persona con conocimientos básicos de sistemas y ciberseguridad que necesita consultar y analizar información externa sin utilizar múltiples herramientas independientes.

La versión inicial no requerirá una organización empresarial, un SOC o una infraestructura de seguridad propia para poder utilizarse.

----------

# 4. Objetivos del producto

## 4.1. Objetivos funcionales

-   Integrar al menos tres fuentes externas de ciberseguridad.
    
-   Centralizar vulnerabilidades e indicadores de compromiso.
    
-   Mantener los datos en una base de datos persistente.
    
-   Permitir búsquedas por tipo de indicador y por identificador CVE.
    
-   Conservar la procedencia de cada observación.
    
-   Detectar duplicados y actualizar registros existentes.
    
-   Mostrar el estado de las fuentes y el historial de ingesta.
    
-   Proporcionar una API REST documentada.
    
-   Presentar los datos mediante un dashboard web.
    

## 4.2. Objetivos técnicos y académicos

El proyecto debe demostrar:

-   Consumo de APIs REST y feeds públicos.
    
-   Manejo de JSON y validación de datos.
    
-   Programación asíncrona con Python.
    
-   Diseño de una API con FastAPI.
    
-   Persistencia relacional con PostgreSQL.
    
-   Uso de migraciones de base de datos.
    
-   Normalización y deduplicación de información.
    
-   Pruebas unitarias y de integración.
    
-   Separación de responsabilidades en una arquitectura modular.
    
-   Documentación y despliegue reproducible.
    

## 4.3. Objetivos que no se asumirán

GTIP no pretende garantizar la detección de todos los ataques existentes, determinar con certeza si un indicador está realizando un ataque en tiempo real ni sustituir una solución de seguridad empresarial.

----------

# 5. Alcance del producto

## 5.1. Incluido en el MVP

Módulo

Alcance

Integración de fuentes

Tres conectores funcionales como mínimo

Ingesta

Ejecución manual y periódica

Vulnerabilidades

Catálogo CVE y estado KEV

Indicadores

IP, dominio, URL y hash

Normalización

Formato común y validación

Persistencia

PostgreSQL

Búsqueda

Consulta de CVE e IOC

Correlación

Agrupación por indicador y fuente

Dashboard

Estadísticas y actividad reciente

Supervisión

Estado e historial de ingesta

API propia

Endpoints REST documentados

Calidad

Pruebas automatizadas y manejo de errores

Despliegue

Docker Compose y documentación

## 5.2. Fuera del MVP

Las siguientes funciones no serán necesarias para considerar completada la primera versión:

-   Captura y análisis de tráfico de red en tiempo real.
    
-   Ingesta generalizada de logs de endpoints y servidores.
    
-   Reglas de detección sobre logs internos.
    
-   Respuesta automática a incidentes.
    
-   Ejecución o análisis dinámico de malware.
    
-   Escaneo activo de sistemas de terceros.
    
-   Predicción de ataques mediante inteligencia artificial.
    
-   Aprendizaje automático para clasificar malware.
    
-   Infraestructura distribuida con Kubernetes.
    
-   Integración con plataformas empresariales de SOAR.
    
-   Gestión avanzada de usuarios, equipos y permisos.
    
-   Suscripciones comerciales y facturación.
    

Estas funciones podrán evaluarse en versiones futuras si existe una necesidad real.

----------

# 6. Fuentes externas y APIs

La plataforma utilizará fuentes complementarias. Cada una aportará información diferente.

## 6.1. CISA Known Exploited Vulnerabilities (KEV)

**Sitio:**  [https://www.cisa.gov/known-exploited-vulnerabilities-catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)

**Función:** proporcionar un catálogo de vulnerabilidades que se sabe que han sido explotadas.

**Datos relevantes:**

-   Identificador CVE.
    
-   Proveedor y producto afectados.
    
-   Nombre de la vulnerabilidad.
    
-   Fecha de incorporación al catálogo.
    
-   Fecha límite de remediación, cuando corresponda.
    
-   Acción de remediación recomendada.
    
-   Indicador de vulnerabilidad explotada conocida.
    

**Integración prevista:** descargar el catálogo JSON, validar los registros y actualizar el catálogo interno de vulnerabilidades.

**Autenticación:** el feed público seleccionado no requiere una clave API.

## 6.2. National Vulnerability Database (NVD)

**Documentación:**  [https://nvd.nist.gov/developers/vulnerabilities](https://nvd.nist.gov/developers/vulnerabilities)

**Función:** enriquecer el catálogo de vulnerabilidades con información técnica.

**Datos relevantes:**

-   Identificador CVE.
    
-   Descripción.
    
-   Fecha de publicación.
    
-   Fecha de modificación.
    
-   Puntuación CVSS, cuando esté disponible.
    
-   Vector CVSS y referencias técnicas.
    
-   Información de productos afectados, cuando esté disponible.
    

**Integración prevista:** consultar la API 2.0, procesar resultados paginados y actualizar las vulnerabilidades nuevas o modificadas.

**Autenticación:** admite acceso sin clave para uso básico; una clave permite obtener una cuota superior conforme a las condiciones del proveedor.

## 6.3. URLhaus

**Documentación:**  [https://urlhaus.abuse.ch/api/](https://urlhaus.abuse.ch/api/)

**Función:** obtener información sobre URLs relacionadas con distribución de malware.

**Datos relevantes:**

-   URL reportada.
    
-   Identificador externo.
    
-   Fecha de registro.
    
-   Estado disponible del indicador.
    
-   Categoría o etiquetas disponibles.
    
-   Referencias relacionadas con malware.
    

**Integración prevista:** utilizar un feed o endpoint apropiado de acuerdo con la documentación, normalizar las URLs y registrar su procedencia.

**Autenticación:** dependerá del endpoint o feed elegido. Se respetarán los requisitos de autenticación y uso de la fuente.

## 6.4. AbuseIPDB

**Documentación:**  [https://docs.abuseipdb.com/](https://docs.abuseipdb.com/)

**Función:** consultar la reputación de direcciones IP y los reportes comunitarios de actividad abusiva.

**Datos relevantes:**

-   Dirección IP.
    
-   Indicador de confianza de abuso reportado.
    
-   Cantidad de reportes disponibles.
    
-   Fecha del último reporte.
    
-   País o proveedor de red, cuando se proporcione.
    
-   Categorías de abuso reportadas.
    

**Integración prevista:** consulta bajo demanda cuando el usuario investigue una IP o cuando una tarea controlada necesite enriquecer un indicador.

**Autenticación:** requiere una clave API y está sujeto a cuotas y condiciones de uso.

## 6.5. AlienVault Open Threat Exchange (OTX)

**Documentación:**  [https://otx.alienvault.com/api](https://otx.alienvault.com/api)

**Función:** ampliar la inteligencia disponible con indicadores y colecciones de información conocidas como _pulses_.

**Datos relevantes:**

-   Indicadores.
    
-   Identificadores de pulses.
    
-   Descripciones.
    
-   Fechas disponibles.
    
-   Referencias y contexto publicado por la comunidad.
    

**Integración prevista:** consultar los recursos seleccionados, validar las respuestas y relacionar los indicadores con los ya almacenados.

**Autenticación:** se utilizará la autenticación requerida por la API seleccionada.

## 6.6. Orden de implementación

1.  CISA KEV.
    
2.  NVD.
    
3.  URLhaus.
    
4.  AbuseIPDB.
    
5.  AlienVault OTX.
    

Las tres primeras serán el objetivo mínimo de integración. Las dos últimas se incorporarán después de que el sistema de ingesta y persistencia esté probado.

Los límites, requisitos de autenticación y formatos de cada fuente se verificarán durante la implementación. No se asumirán cuotas, disponibilidad permanente ni licencias que no estén documentadas.

----------

# 7. Arquitectura técnica

## 7.1. Enfoque arquitectónico

Se utilizará un monolito modular con procesos de ingesta independientes del servidor HTTP.

Esta arquitectura permite mantener el proyecto sencillo de desarrollar y desplegar, pero separa las responsabilidades para facilitar su evolución.

No se implementarán microservicios en el MVP.

## 7.2. Componentes

### A. Conectores externos

Responsables de comunicarse con las APIs y feeds.

Funciones:

-   Construir solicitudes HTTP.
    
-   Gestionar autenticación.
    
-   Configurar timeouts.
    
-   Procesar respuestas.
    
-   Controlar paginación.
    
-   Manejar errores y límites.
    
-   Devolver datos en estructuras que puedan procesarse.
    

Tecnología: HTTPX.

### B. Servicio de ingesta

Coordina la ejecución de cada fuente.

Funciones:

-   Iniciar y finalizar ejecuciones.
    
-   Invocar los conectores.
    
-   Validar resultados.
    
-   Registrar métricas de ingesta.
    
-   Gestionar errores por fuente.
    
-   Actualizar o insertar registros.
    
-   Evitar duplicados.
    

### C. Servicio de normalización

Convierte las estructuras externas a modelos internos.

Funciones:

-   Validar los campos obligatorios.
    
-   Normalizar direcciones IP, dominios, URLs y hashes.
    
-   Convertir fechas.
    
-   Unificar tipos de datos.
    
-   Conservar la referencia al proveedor.
    
-   Rechazar registros inválidos sin detener toda la ingesta.
    

### D. Capa de persistencia

Responsable de almacenar y recuperar información.

Tecnología:

-   PostgreSQL.
    
-   SQLAlchemy 2.
    
-   Alembic.
    

### E. API REST

Expone las funcionalidades de la plataforma.

Tecnología: FastAPI y Pydantic.

Responsabilidades:

-   Recibir solicitudes.
    
-   Validar parámetros.
    
-   Invocar servicios.
    
-   Aplicar paginación y filtros.
    
-   Devolver respuestas consistentes.
    
-   Gestionar errores HTTP.
    

### F. Proceso de tareas programadas

Ejecuta actualizaciones periódicas de fuentes.

Tecnología inicial: APScheduler.

El planificador no deberá bloquear las peticiones HTTP ni ejecutar simultáneamente dos ingestas incompatibles de la misma fuente.

### G. Frontend

Interfaz web para consultar y visualizar los datos.

Tecnología:

-   React.
    
-   TypeScript.
    
-   Recharts para visualizaciones, cuando sea necesario.
    

### H. Infraestructura local

Docker Compose permitirá ejecutar:

-   Backend.
    
-   Base de datos.
    
-   Frontend.
    
-   Proceso de ingesta, si se despliega como proceso separado.
    

----------

# 8. Flujo general de datos

El proceso de ingesta seguirá esta secuencia:

1.  Se inicia una ejecución manual o programada.
    
2.  Se crea un registro en `ingestion_runs`.
    
3.  Se consulta la fuente externa.
    
4.  Se valida la respuesta HTTP.
    
5.  Se interpreta el contenido recibido.
    
6.  Se transforman los registros a esquemas internos.
    
7.  Se validan los datos normalizados.
    
8.  Se insertan los registros nuevos o se actualizan los existentes.
    
9.  Se guardan las observaciones y referencias de procedencia.
    
10.  Se registran las cantidades procesadas y los errores.
    
11.  La ejecución termina con un estado de éxito, parcial o fallo.
    
12.  El frontend consulta los datos persistidos a través de FastAPI.
    

Las búsquedas ordinarias consultarán la base de datos. No se realizarán llamadas a todos los proveedores cada vez que se abra una página.

Las consultas externas bajo demanda, como la reputación de una IP, se ejecutarán mediante un servicio específico que controle cuotas, tiempos de espera y almacenamiento de resultados.

----------

# 9. Modelo de datos

La base de datos utilizará PostgreSQL. Los modelos se implementarán con SQLAlchemy y las modificaciones de esquema se gestionarán mediante Alembic.

## 9.1. Tabla `sources`

Representa cada proveedor de inteligencia.

Campo

Tipo orientativo

Descripción

`id`

UUID

Identificador interno

`name`

VARCHAR

Nombre de la fuente

`source_type`

VARCHAR

Tipo de fuente

`base_url`

TEXT

URL documentada

`enabled`

BOOLEAN

Indica si está habilitada

`last_success_at`

TIMESTAMP

Último éxito

`last_error`

TEXT nullable

Último error registrado

`created_at`

TIMESTAMP

Fecha de creación

## 9.2. Tabla `vulnerabilities`

Representa una vulnerabilidad identificada por CVE.

Campo

Tipo orientativo

Descripción

`id`

UUID

Identificador interno

`cve_id`

VARCHAR UNIQUE

Identificador CVE

`description`

TEXT

Descripción disponible

`cvss_score`

NUMERIC nullable

Puntuación CVSS

`cvss_vector`

TEXT nullable

Vector CVSS

`published_at`

TIMESTAMP nullable

Fecha de publicación

`modified_at`

TIMESTAMP nullable

Fecha de modificación

`is_kev`

BOOLEAN

Presencia confirmada en KEV

`kev_added_at`

DATE nullable

Fecha de incorporación al catálogo

`created_at`

TIMESTAMP

Creación interna

`updated_at`

TIMESTAMP

Última actualización interna

Las puntuaciones CVSS se almacenarán junto con su versión o contexto cuando corresponda. Un dato ausente no se convertirá en cero.

La presencia en KEV deberá actualizarse a partir de una sincronización válida del catálogo, no por la ausencia de un registro en una respuesta parcial.

## 9.3. Tabla `indicators`

Representa la identidad normalizada de un indicador de compromiso.

Campo

Tipo orientativo

Descripción

`id`

UUID

Identificador interno

`type`

VARCHAR

Tipo de IOC

`value`

TEXT

Valor presentado

`normalized_value`

TEXT

Valor normalizado

`created_at`

TIMESTAMP

Fecha de creación

Tipos iniciales admitidos:

-   `ipv4`
    
-   `ipv6`
    
-   `domain`
    
-   `url`
    
-   `md5`
    
-   `sha1`
    
-   `sha256`
    

La normalización dependerá del tipo. Los dominios pueden normalizarse a minúsculas, mientras que las URLs requieren conservar las diferencias relevantes de ruta y parámetros. Los hashes deben validarse según su longitud y representación.

## 9.4. Tabla `observations`

Representa la evidencia aportada por una fuente sobre un indicador.

Campo

Tipo orientativo

Descripción

`id`

UUID

Identificador interno

`source_id`

UUID FK

Fuente de procedencia

`indicator_id`

UUID FK

Indicador relacionado

`external_id`

VARCHAR nullable

Identificador externo

`first_seen_at`

TIMESTAMP nullable

Primera fecha reportada

`last_seen_at`

TIMESTAMP nullable

Última fecha reportada

`observed_at`

TIMESTAMP

Fecha de consulta u observación

`raw_data`

JSONB

Datos originales relevantes

Una observación no implica que el indicador sea malicioso en el momento actual. Representa un dato publicado o devuelto por una fuente en un contexto temporal determinado.

Cuando una fuente tenga un identificador externo estable, se utilizará una restricción única adecuada para impedir duplicados.

## 9.5. Tabla `ingestion_runs`

Registra la ejecución de una tarea de ingesta.

Campo

Tipo orientativo

Descripción

`id`

UUID

Identificador de ejecución

`source_id`

UUID FK

Fuente procesada

`started_at`

TIMESTAMP

Inicio

`finished_at`

TIMESTAMP nullable

Finalización

`status`

VARCHAR

Estado

`records_received`

INTEGER

Registros recibidos

`records_saved`

INTEGER

Registros insertados o actualizados

`error_message`

TEXT nullable

Resumen del error

Estados permitidos:

-   `running`
    
-   `success`
    
-   `partial`
    
-   `failed`
    

## 9.6. Relaciones

-   Una fuente puede producir muchas observaciones.
    
-   Un indicador puede tener muchas observaciones.
    
-   Una fuente puede tener muchas ejecuciones de ingesta.
    
-   Una vulnerabilidad tiene un identificador CVE único.
    
-   Las observaciones pueden relacionarse con indicadores sin que eso implique una relación automática con una vulnerabilidad.
    

La relación entre vulnerabilidades e indicadores se añadirá únicamente cuando una fuente proporcione evidencia explícita que la sustente.

## 9.7. Índices y restricciones

Se definirán:

-   Índice único para `vulnerabilities.cve_id`.
    
-   Índice para `indicators.type` y `indicators.normalized_value`.
    
-   Restricción única para la identidad normalizada del indicador, según las reglas de normalización.
    
-   Índices sobre `observations.source_id` e `indicator_id`.
    
-   Restricción única sobre identificadores externos estables por fuente.
    
-   Índices sobre las fechas de publicación y modificación de vulnerabilidades.
    

----------

# 10. Módulos funcionales

## 10.1. Dashboard

### Objetivo

Mostrar un resumen de los datos recopilados y del estado operativo de la plataforma.

### Funciones

-   Total de vulnerabilidades almacenadas.
    
-   Cantidad de vulnerabilidades presentes en KEV.
    
-   Total de indicadores únicos.
    
-   Observaciones recientes.
    
-   Últimas ejecuciones de ingesta.
    
-   Estado de las fuentes.
    
-   Distribución de vulnerabilidades por puntuación CVSS, cuando haya datos disponibles.
    

### Criterios de aceptación

-   Los valores proceden de la base de datos.
    
-   Los filtros y las estadísticas reflejan datos reales.
    
-   Se muestra cuándo se actualizaron las fuentes.
    
-   Los valores desconocidos no se presentan como cero sin distinción.
    

## 10.2. Catálogo de vulnerabilidades

### Objetivo

Permitir consultar y priorizar vulnerabilidades conocidas.

### Funciones

-   Listado paginado de CVE.
    
-   Búsqueda por identificador.
    
-   Filtro por puntuación CVSS.
    
-   Filtro por presencia en KEV.
    
-   Orden por fecha de publicación o modificación.
    
-   Vista de detalle con descripción, referencias y fechas.
    
-   Visualización de datos de procedencia.
    

### Criterios de aceptación

-   La búsqueda por CVE devuelve el registro correcto cuando existe.
    
-   Se distinguen puntuaciones ausentes de puntuaciones reales.
    
-   La presencia en KEV se actualiza mediante el catálogo sincronizado.
    
-   Las referencias permiten identificar la fuente de la información.
    

## 10.3. Buscador de IOC

### Objetivo

Facilitar la investigación de indicadores.

### Funciones

-   Búsqueda de IP, dominio, URL y hash.
    
-   Validación del formato del indicador.
    
-   Consulta de los indicadores almacenados.
    
-   Listado de observaciones relacionadas.
    
-   Visualización de fuentes y fechas.
    
-   Consulta bajo demanda de reputación cuando el proveedor lo permita.
    

### Criterios de aceptación

-   Las búsquedas no ejecutan peticiones externas indiscriminadas.
    
-   Los resultados identifican sus fuentes.
    
-   Los indicadores sin coincidencias se muestran como no encontrados, no como seguros.
    
-   Se informa de cuándo un resultado procede de datos almacenados y cuándo de una consulta externa.
    

## 10.4. Correlación de amenazas

### Objetivo

Agrupar las observaciones relacionadas con el mismo indicador.

### Primera versión

-   Detectar indicadores duplicados entre fuentes.
    
-   Agrupar sus observaciones.
    
-   Mostrar la cantidad de fuentes que aportan datos.
    
-   Mostrar referencias, fechas y diferencias entre los reportes.
    

### Limitaciones

La coincidencia de un indicador no demuestra por sí sola que dos reportes pertenezcan a una misma campaña o grupo de atacantes.

La primera versión no realizará atribución de actores de amenazas ni inferirá causalidad.

## 10.5. Monitor de fuentes

### Objetivo

Permitir comprobar la disponibilidad y el historial de los proveedores integrados.

### Funciones

-   Listado de fuentes habilitadas.
    
-   Última ingesta exitosa.
    
-   Estado de la última ejecución.
    
-   Registros procesados.
    
-   Errores recientes.
    
-   Solicitud de una ingesta manual autorizada.
    

Una fuente se considerará operativa según los resultados de sus últimas ejecuciones, no simplemente porque exista una configuración.

## 10.6. API pública del proyecto

La API propia permitirá consultar los datos normalizados y podrá utilizarse desde otras aplicaciones.

En el MVP, los endpoints de lectura podrán exponerse para el entorno de demostración. Los endpoints administrativos estarán protegidos si se despliega el servicio en una red accesible.

----------

# 11. Diseño de la API REST

Prefijo general: `/api/v1`.

## 11.1. Endpoints

Método

Endpoint

Descripción

GET

`/health`

Estado de aplicación y base de datos

GET

`/sources`

Listar fuentes

GET

`/sources/{source_id}`

Detalle de fuente

GET

`/dashboard/summary`

Estadísticas generales

GET

`/vulnerabilities`

Listar y filtrar CVE

GET

`/vulnerabilities/{cve_id}`

Detalle de CVE

GET

`/indicators`

Buscar indicadores almacenados

GET

`/indicators/{indicator_id}`

Detalle del indicador

GET

`/indicators/{indicator_id}/observations`

Evidencias por fuente

GET

`/search?q={query}`

Búsqueda unificada

GET

`/ingestion/runs`

Historial de ingestas

POST

`/ingestion/runs`

Solicitar una ingesta manual

Los endpoints administrativos de ingesta deberán requerir autorización cuando el servicio no esté limitado al entorno local.

## 11.2. Parámetros de consulta

Para vulnerabilidades:

-   `q`: texto o identificador CVE.
    
-   `is_kev`: filtrar por presencia en KEV.
    
-   `min_cvss`: puntuación mínima.
    
-   `published_after`: fecha inicial.
    
-   `published_before`: fecha final.
    
-   `page`: número de página.
    
-   `page_size`: cantidad de resultados.
    

Para indicadores:

-   `type`: tipo de indicador.
    
-   `value`: valor buscado.
    
-   `source_id`: fuente de observación.
    
-   `page`: número de página.
    
-   `page_size`: cantidad de resultados.
    

Se aplicará un máximo configurable de resultados por página.

## 11.3. Formato de respuesta

Las respuestas utilizarán JSON.

Ejemplo conceptual:

{  
"items": [  
{  
"cve_id": "CVE-2025-0000",  
"description": "Ejemplo de descripción",  
"cvss_score": null,  
"is_kev": false  
}  
],  
"page": 1,  
"page_size": 20,  
"total": 1  
}

Este ejemplo ilustra el formato y no representa datos reales de una vulnerabilidad.

Los errores utilizarán códigos HTTP apropiados y mensajes consistentes. Las respuestas no incluirán claves API, secretos ni trazas internas.

----------

# 12. Estrategia de ingesta y actualización

## 12.1. Actualización periódica

Cada fuente tendrá un intervalo configurable, definido de acuerdo con su frecuencia de actualización y sus límites de uso.

Los intervalos iniciales serán valores de configuración y no garantías sobre la frecuencia de publicación del proveedor.

## 12.2. Idempotencia

La repetición de una ingesta no debe generar registros duplicados.

Se utilizarán claves únicas, operaciones de actualización y reglas de identificación propias de cada fuente.

## 12.3. Actualización incremental

Cuando el proveedor admita filtros de modificación, marcas de tiempo o paginación incremental, se aprovecharán para evitar descargar información innecesaria.

Para fuentes sin soporte incremental adecuado, se utilizará la estrategia de sincronización compatible con su documentación.

## 12.4. Errores

Los errores se clasificarán según su naturaleza:

-   Errores de conexión.
    
-   Timeouts.
    
-   Respuestas HTTP de error.
    
-   Límites de cuota.
    
-   Fallos de autenticación.
    
-   Respuestas inválidas.
    
-   Errores de validación.
    
-   Errores de base de datos.
    

Los errores transitorios podrán reintentarse con espera exponencial y límites. Los errores de autenticación no deberán provocar reintentos indefinidos.

## 12.5. Fallos parciales

Una fuente que falle no debe impedir que las demás se procesen.

Cada ejecución tendrá su propio registro y estado. Una respuesta incompleta no deberá interpretarse automáticamente como una eliminación de todos los datos previamente almacenados.

----------

# 13. Estructura del repositorio

```
global-threat-intel/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── api/
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── health.py
│   │           ├── sources.py
│   │           ├── indicators.py
│   │           ├── vulnerabilities.py
│   │           ├── search.py
│   │           └── ingestion.py
│   ├── connectors/
│   │   ├── base.py
│   │   ├── cisa_kev.py
│   │   ├── nvd.py
│   │   ├── urlhaus.py
│   │   ├── abuseipdb.py
│   │   └── otx.py
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   │   ├── ingestion.py
│   │   ├── normalization.py
│   │   └── correlation.py
│   ├── db/
│   │   ├── session.py
│   │   └── base.py
│   └── workers/
│       └── scheduler.py
├── migrations/
├── tests/
│   ├── connectors/
│   ├── services/
│   └── api/
├── frontend/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

Los módulos se crearán progresivamente. No será necesario implementar todas las carpetas antes de tener la primera integración funcionando.

----------

# 14. Stack tecnológico

## Backend

-   Python 3.12 o superior compatible con las dependencias seleccionadas.
    
-   FastAPI.
    
-   Uvicorn.
    
-   HTTPX.
    
-   Pydantic.
    
-   SQLAlchemy 2.
    
-   Alembic.
    

## Base de datos

-   PostgreSQL.
    
-   JSONB para almacenar respuestas originales relevantes.
    
-   Índices y restricciones para mejorar las consultas y garantizar integridad.
    

## Procesamiento periódico

-   APScheduler para el MVP.
    
-   Un proceso de trabajo separado del servidor HTTP cuando se despliegue con Docker Compose.
    

No se utilizarán colas distribuidas ni sistemas de mensajería hasta que el volumen de datos justifique su complejidad.

## Frontend

-   React.
    
-   TypeScript.
    
-   Una herramienta de construcción como Vite.
    
-   Recharts para las gráficas necesarias.
    
-   Cliente HTTP para comunicarse con FastAPI.
    

## Pruebas

-   Pytest.
    
-   Respx para simular solicitudes HTTP.
    
-   Pruebas de integración con PostgreSQL.
    
-   Pruebas del frontend según los componentes desarrollados.
    

## Despliegue

-   Docker.
    
-   Docker Compose.
    
-   Variables de entorno.
    
-   README de instalación y ejecución.
    

Las versiones concretas se fijarán en el proyecto para favorecer una instalación reproducible.

----------

# 15. Requisitos no funcionales

## 15.1. Rendimiento

-   Las búsquedas habituales se realizarán sobre la base de datos.
    
-   Los listados utilizarán paginación.
    
-   Las solicitudes externas tendrán timeouts.
    
-   Las consultas se optimizarán con índices cuando corresponda.
    
-   El sistema deberá evitar descargar grandes conjuntos de datos en cada petición del frontend.
    

Como objetivo inicial de desarrollo, se buscará que las consultas locales habituales respondan en menos de un segundo con un conjunto de datos de prueba moderado. Este objetivo se validará mediante pruebas; no representa una garantía de rendimiento en producción.

## 15.2. Disponibilidad y tolerancia a fallos

-   Una fuente caída no bloqueará las demás.
    
-   Los errores externos quedarán registrados.
    
-   La aplicación podrá seguir consultando los datos previamente almacenados si una fuente no está disponible.
    
-   Los fallos de ingesta no provocarán la eliminación accidental de información válida.
    

## 15.3. Seguridad

-   Las claves API se almacenarán en variables de entorno.
    
-   Los secretos no se subirán al repositorio.
    
-   Los endpoints administrativos requerirán autorización fuera del entorno local.
    
-   Se validarán las entradas de los usuarios.
    
-   Se limitarán los tamaños de respuesta y las solicitudes que puedan consumir recursos excesivos.
    
-   Se utilizarán consultas parametrizadas mediante el ORM.
    
-   Los logs no incluirán credenciales ni secretos.
    
-   El acceso a servicios externos se realizará mediante HTTPS cuando esté disponible.
    

Las URLs o indicadores consultados deben tratarse como datos no confiables. La plataforma no abrirá automáticamente URLs maliciosas en el navegador del usuario ni ejecutará contenido recibido de las fuentes.

## 15.4. Mantenibilidad

-   Los conectores estarán separados de los servicios y de la API.
    
-   Las responsabilidades estarán definidas por módulo.
    
-   La configuración se gestionará de forma centralizada.
    
-   Las migraciones de base de datos estarán versionadas.
    
-   Los contratos de los endpoints estarán documentados.
    
-   Los errores y las decisiones de normalización estarán documentados.
    

## 15.5. Reproducibilidad

Otra persona deberá poder ejecutar el proyecto siguiendo el README, configurar sus propias credenciales y realizar una demostración local sin depender de configuraciones particulares de la máquina del desarrollador.

----------

# 16. Seguridad y tratamiento responsable de datos

GTIP será una herramienta de consulta y análisis de información pública.

El proyecto no incluirá funciones para atacar sistemas, evadir controles, explotar vulnerabilidades o realizar escaneos indiscriminados de terceros.

Se aplicarán las siguientes reglas:

1.  Respetar los términos de uso y las cuotas de cada proveedor.
    
2.  No publicar claves API en el frontend.
    
3.  No asumir que una dirección IP reportada es necesariamente maliciosa.
    
4.  Mostrar la fecha y la fuente de los reportes.
    
5.  No atribuir campañas o actores de amenazas sin evidencia suficiente.
    
6.  Evitar que una URL recibida de una fuente se convierta automáticamente en una solicitud saliente.
    
7.  No almacenar más datos personales de los necesarios para la finalidad del proyecto.
    
8.  Proteger los endpoints de ingesta y administración.
    

Las consultas externas se limitarán a los indicadores necesarios para las funciones del sistema y estarán sujetas a las políticas de cada proveedor.

----------

# 17. Diseño de interfaz

La interfaz será una aplicación web con navegación lateral y un diseño orientado a la investigación técnica.

## 17.1. Navegación principal

-   Dashboard.
    
-   Vulnerabilidades.
    
-   Indicadores.
    
-   Búsqueda.
    
-   Fuentes de inteligencia.
    
-   Historial de ingesta.
    
-   Configuración técnica.
    

## 17.2. Dashboard

Incluirá:

-   Tarjetas de estadísticas.
    
-   Últimas vulnerabilidades registradas.
    
-   Indicadores recientes.
    
-   Estado de las fuentes.
    
-   Últimas ejecuciones.
    
-   Gráficas basadas en los datos disponibles.
    

No se mostrarán mapas globales de ataques ni cifras geográficas inventadas. Una visualización geográfica solo se incorporará si las fuentes proporcionan datos adecuados y se explica qué representan.

## 17.3. Página de vulnerabilidades

Mostrará una tabla con:

-   CVE.
    
-   Descripción resumida.
    
-   Puntuación CVSS, cuando exista.
    
-   Presencia en KEV.
    
-   Fecha de publicación.
    
-   Fecha de modificación.
    

Permitirá buscar, filtrar y ordenar los resultados.

## 17.4. Página de indicadores

Permitirá introducir un indicador y consultar:

-   Tipo y valor.
    
-   Coincidencias almacenadas.
    
-   Fuentes relacionadas.
    
-   Fechas de observación.
    
-   Datos de reputación disponibles.
    
-   Referencias para ampliar la investigación.
    

## 17.5. Página de fuentes

Mostrará el nombre del proveedor, su estado de integración, la última ejecución y el resultado de la sincronización.

El estado de una fuente representará el resultado técnico de la ingesta, no la certeza de que sus datos sean correctos o completos.

----------

# 18. Plan de desarrollo

La planificación inicial será de seis semanas. El tiempo podrá variar según la experiencia del desarrollador, las restricciones de las APIs y los requisitos de la asignatura.

## Semana 1 — Fundamentos y CISA KEV

Tareas:

-   Crear el repositorio.
    
-   Configurar el entorno Python.
    
-   Crear la aplicación FastAPI.
    
-   Configurar HTTPX y Pydantic.
    
-   Implementar el primer conector.
    
-   Crear un endpoint de prueba.
    
-   Documentar cómo se ejecuta el backend.
    

Entregable: aplicación funcional que consulta el catálogo CISA y devuelve resultados válidos.

## Semana 2 — PostgreSQL y NVD

Tareas:

-   Configurar PostgreSQL.
    
-   Implementar SQLAlchemy.
    
-   Crear las primeras migraciones con Alembic.
    
-   Diseñar los modelos de fuente y vulnerabilidad.
    
-   Integrar NVD.
    
-   Implementar inserciones y actualizaciones idempotentes.
    
-   Añadir pruebas de persistencia.
    

Entregable: dos fuentes integradas con datos persistidos.

## Semana 3 — URLhaus y normalización

Tareas:

-   Crear el modelo de indicadores.
    
-   Implementar el conector URLhaus.
    
-   Normalizar URLs.
    
-   Crear la tabla de observaciones.
    
-   Registrar la procedencia de los datos.
    
-   Implementar el historial de ingesta.
    
-   Añadir manejo de errores y reintentos.
    

Entregable: tres fuentes funcionales y consultables.

## Semana 4 — Búsqueda y correlación

Tareas:

-   Implementar búsqueda por CVE.
    
-   Implementar búsqueda por IOC.
    
-   Agrupar observaciones del mismo indicador.
    
-   Integrar AbuseIPDB bajo demanda, si las credenciales están disponibles.
    
-   Crear endpoints de estadísticas.
    
-   Probar la tolerancia a fallos de los conectores.
    

Entregable: backend de investigación funcional.

## Semana 5 — Frontend

Tareas:

-   Crear la aplicación React.
    
-   Implementar la navegación.
    
-   Construir el dashboard.
    
-   Añadir el catálogo de vulnerabilidades.
    
-   Crear la página de búsqueda de IOC.
    
-   Mostrar fuentes y fechas.
    
-   Conectar el frontend con FastAPI.
    

Entregable: interfaz funcional con datos reales.

## Semana 6 — Pruebas y entrega

Tareas:

-   Completar pruebas unitarias y de integración.
    
-   Simular fallos de proveedores.
    
-   Configurar Docker Compose.
    
-   Revisar las variables de entorno.
    
-   Documentar instalación y arquitectura.
    
-   Preparar datos de demostración.
    
-   Preparar una presentación del proyecto.
    

Entregable: MVP reproducible y documentado.

OTX se considerará una integración adicional si el núcleo está terminado. No se comprometerá la entrega por intentar incorporar una quinta fuente antes de validar las tres primeras.

----------

# 19. Pruebas y criterios de aceptación

## 19.1. Conectores

-   Cada conector interpreta correctamente una respuesta válida.
    
-   Las respuestas inválidas se manejan sin bloquear la aplicación.
    
-   Los errores HTTP se registran.
    
-   Los timeouts están configurados.
    
-   Las pruebas automatizadas no dependen de que el proveedor externo esté disponible.
    

## 19.2. Persistencia

-   Las vulnerabilidades tienen identificadores CVE únicos.
    
-   Las reingestas no generan duplicados.
    
-   Los indicadores iguales bajo las reglas de normalización se relacionan correctamente.
    
-   Las observaciones conservan su fuente.
    
-   Las migraciones pueden ejecutarse desde una base de datos nueva.
    

## 19.3. API

-   Los endpoints devuelven JSON válido.
    
-   Los parámetros incorrectos producen errores HTTP apropiados.
    
-   Los listados admiten paginación.
    
-   Las búsquedas distinguen entre resultados inexistentes y errores de consulta.
    
-   Los endpoints administrativos están protegidos cuando corresponde.
    

## 19.4. Interfaz

-   Las estadísticas reflejan datos persistidos.
    
-   El usuario puede consultar vulnerabilidades.
    
-   El usuario puede buscar indicadores.
    
-   Los detalles muestran procedencia y fechas.
    
-   Los errores de carga se comunican de forma comprensible.
    

## 19.5. Despliegue

-   El proyecto arranca siguiendo el README.
    
-   Los secretos no están incluidos en el repositorio.
    
-   La base de datos puede inicializarse desde cero.
    
-   La aplicación puede demostrarse con datos reales o con fixtures claramente identificados.
    
-   Una caída simulada de un proveedor no impide consultar los datos almacenados.
    

----------

# 20. Métricas de éxito

El éxito del MVP se medirá por criterios verificables.

Métrica

Objetivo inicial

Fuentes integradas

3 como mínimo

Persistencia

Funcional en PostgreSQL

Duplicados en reingestas

Sin duplicados bajo las restricciones definidas

Búsqueda de CVE

Funcional

Búsqueda de IOC

Funcional

Procedencia

Disponible en las observaciones

Historial de ingesta

Disponible para cada fuente

Pruebas automatizadas

Cubren conectores y servicios principales

Documentación

Instalación, arquitectura y endpoints documentados

Despliegue

Reproducible mediante Docker Compose

La cantidad de registros recopilados no será una métrica aislada de calidad: dependerá de las fuentes, sus cuotas y el momento de la sincronización.

----------

# 21. Riesgos y mitigaciones

## APIs no disponibles

**Riesgo:** un proveedor puede fallar o cambiar su respuesta.

**Mitigación:** timeouts, reintentos limitados, validación de esquemas y persistencia de los datos previamente almacenados.

## Cuotas insuficientes

**Riesgo:** una fuente puede limitar las consultas.

**Mitigación:** actualización periódica, consultas bajo demanda, almacenamiento en caché y respeto de las cuotas.

## Datos incompatibles

**Riesgo:** cada fuente utiliza campos y formatos diferentes.

**Mitigación:** conectores independientes, esquemas Pydantic y normalización centralizada.

## Duplicación de información

**Riesgo:** múltiples fuentes pueden reportar el mismo indicador.

**Mitigación:** identidad normalizada, restricciones únicas y observaciones independientes por fuente.

## Falsos positivos

**Riesgo:** un indicador puede estar reportado por actividad antigua o por errores de clasificación.

**Mitigación:** conservar fechas, procedencia y contexto; no presentar los resultados como certezas absolutas.

## Exceso de alcance

**Riesgo:** intentar construir un SIEM completo en seis semanas.

**Mitigación:** limitar el MVP a inteligencia externa, tres fuentes, búsqueda, persistencia y un dashboard.

## Falta de tiempo para el frontend

**Riesgo:** la integración técnica consume más tiempo del previsto.

**Mitigación:** priorizar el backend y construir primero una interfaz mínima, antes de añadir visualizaciones complejas.

----------

# 22. Versiones futuras

Una vez completado el MVP, podrán evaluarse nuevas funcionalidades.

## Versión 1.1 — Enriquecimiento

-   Integración completa de AbuseIPDB y OTX.
    
-   Mejoras en el historial de observaciones.
    
-   Filtros avanzados.
    
-   Exportación de resultados seleccionados.
    
-   Mejoras de rendimiento.
    

## Versión 1.2 — Alertas

-   Reglas configurables para indicadores nuevos.
    
-   Notificaciones cuando aparezcan determinadas vulnerabilidades.
    
-   Alertas sobre fuentes que fallen repetidamente.
    
-   Historial de alertas.
    

## Versión 2.0 — Correlación avanzada

-   Relaciones explícitas entre indicadores.
    
-   Visualización de grafos de evidencia.
    
-   Enriquecimiento con otras fuentes.
    
-   Reglas de correlación configurables.
    
-   API para integraciones externas.
    

## Posible evolución hacia un SIEM

Si el proyecto evoluciona hacia un SIEM, será necesario incorporar una canalización de ingesta de logs internos, normalización de eventos, reglas de detección, correlación temporal y mecanismos de investigación de incidentes.

Esa evolución constituiría una ampliación sustancial del producto, no una función que se dará por implementada en el MVP.

----------

# 23. Entregables académicos

Al finalizar el proyecto se entregarán:

1.  Repositorio del código fuente.
    
2.  Backend FastAPI funcional.
    
3.  Integración de al menos tres fuentes externas.
    
4.  Base de datos PostgreSQL y migraciones.
    
5.  Frontend web.
    
6.  Pruebas automatizadas.
    
7.  Archivo Docker Compose.
    
8.  Documentación de instalación.
    
9.  Documentación de la API.
    
10.  Diagrama de arquitectura.
    
11.  Diagrama del modelo de datos.
    
12.  Evidencias de ejecución y pruebas.
    
13.  Presentación de la demostración funcional.
    

La documentación deberá diferenciar claramente las funcionalidades implementadas de las propuestas para versiones futuras.

----------

# 24. Demostración final

La demostración académica seguirá un flujo completo.

1.  Iniciar el proyecto mediante Docker Compose.
    
2.  Mostrar las fuentes configuradas.
    
3.  Ejecutar una ingesta.
    
4.  Consultar los registros almacenados en PostgreSQL.
    
5.  Mostrar vulnerabilidades obtenidas desde CISA KEV y NVD.
    
6.  Buscar un indicador registrado por URLhaus.
    
7.  Mostrar la procedencia y las fechas de sus observaciones.
    
8.  Simular un fallo de una fuente.
    
9.  Demostrar que la aplicación conserva los datos previamente almacenados.
    
10.  Mostrar las pruebas automatizadas y la documentación.
    

El objetivo de la demostración será comprobar que el sistema integra datos externos de principio a fin, no solamente que el dashboard tiene una apariencia funcional.

----------

# 25. Definición final del producto

Global Threat Intelligence Platform será una aplicación web de inteligencia de amenazas que integra información pública de múltiples fuentes, la normaliza y la conserva en una base de datos propia para facilitar su búsqueda y análisis.

Su primera versión estará orientada a vulnerabilidades e indicadores de compromiso, con un dashboard, una API REST, historial de ingesta y correlación básica por indicador.

El producto priorizará la trazabilidad, la calidad de los datos y la integración funcional frente a la cantidad de características.

**Criterio definitivo de éxito:** un usuario debe poder consultar información procedente de varias fuentes desde una sola aplicación, identificar de dónde viene cada resultado y acceder a una representación organizada de esa información sin tener que consultar manualmente cada proveedor.

----------

# 26. Primer hito de implementación

El primer hito será construir un flujo vertical completo con CISA KEV:

1.  Crear el proyecto Python y FastAPI.
    
2.  Implementar el conector HTTPX.
    
3.  Validar la respuesta con Pydantic.
    
4.  Crear la tabla de vulnerabilidades.
    
5.  Guardar y actualizar registros en PostgreSQL.
    
6.  Exponer `GET /api/v1/vulnerabilities`.
    
7.  Añadir una prueba automatizada.
    
8.  Documentar cómo ejecutar el sistema.
    

Este hito será la base técnica sobre la que se incorporarán NVD, URLhaus, los indicadores y el frontend.

No se comenzará por desarrollar todas las pantallas ni por integrar las cinco APIs a la vez. Primero se comprobará que una fuente puede recorrer correctamente todo el proceso de obtención, validación, persistencia y consulta. Después se ampliará el sistema de manera incremental.