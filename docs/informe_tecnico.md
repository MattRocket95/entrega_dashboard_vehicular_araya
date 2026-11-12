# Informe técnico - Dashboard Operativo Vehicular

## 1. Descripción

Se desarrolló una aplicación web operativa utilizando Python y Streamlit, conectada a Supabase como plataforma de base de datos y almacenamiento.

El objetivo es centralizar la información de vehículos, conductores, autorizaciones e inspecciones, permitiendo separar las necesidades de Puesto de Mando, Guardia de Garita y Conductor Operativo.

## 2. Arquitectura

La aplicación utiliza Streamlit como capa de interfaz y lógica, Pandas para el tratamiento de datos y Supabase como backend.

El flujo principal es:

1. Streamlit obtiene las credenciales desde `st.secrets`.
2. Se establece conexión con Supabase.
3. Se consultan las tablas operativas.
4. El usuario selecciona un perfil de prueba.
5. La interfaz se renderiza de acuerdo con el perfil.
6. Los registros de inspección se almacenan en `reportes_estado`.
7. Las evidencias fotográficas se almacenan en Supabase Storage.

## 3. Lógica de negocio

### Guardia

La vista permite seleccionar un vehículo y un conductor. El sistema consulta las autorizaciones vigentes y revisa además el estado operativo del vehículo.

La respuesta visual distingue entre autorización válida, ausencia de autorización y alerta asociada al estado del vehículo.

### Conductor

El formulario registra kilometraje, combustible, neumáticos, luces y observaciones.

Si se detecta una condición crítica mediante las observaciones, el estado puede pasar a `Crítico`. Si se detecta una condición operacional fuera de norma, como neumáticos o luces en estado no conforme, el vehículo puede pasar a `Requiere Mantención`.

### Administrador

El administrador dispone de indicadores operativos, matriz de estado, analítica de kilometraje, frecuencia de inspecciones y auditoría histórica por patente.

## 4. Evidencia fotográfica

La aplicación valida el tamaño del archivo antes de realizar la carga. El límite utilizado es de 800 KB, de acuerdo con la especificación de la actividad.

## 5. Seguridad

Las credenciales no se incorporan al código fuente. Se utilizan secretos de Streamlit y el archivo correspondiente se excluye mediante `.gitignore`.

El selector de perfiles corresponde a una simulación funcional para la evaluación. No constituye un sistema de autenticación real.

## 6. Validación realizada

Se verificó el funcionamiento de:

- Perfil Administrador.
- Perfil Guardia de Garita.
- Perfil Conductor Operativo.
- Consulta de vehículos y conductores.
- Consulta de autorizaciones.
- Registro de inspecciones.
- Actualización del estado operativo.
- Indicadores de disponibilidad.
- Matriz visual de estado.
- Analítica de kilometraje.
- Frecuencia de inspecciones.
- Auditoría histórica por patente.

## 7. Conclusión

La solución permite centralizar el control operacional vehicular en una interfaz única, manteniendo la información estructurada en Supabase y diferenciando las vistas según el rol operativo. La arquitectura queda preparada para una futura implementación de autenticación real, RLS y despliegue en nube.
