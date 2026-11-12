# Dashboard Operativo Vehicular

Aplicación desarrollada en Python y Streamlit para la consulta, control y seguimiento del material rodante mediante una base de datos Supabase.

## 1. Objetivo

El sistema integra tres perfiles operativos:

- Administrador de Puesto de Mando
- Guardia de Garita
- Conductor Operativo

La aplicación permite consultar vehículos y conductores, validar autorizaciones, registrar inspecciones, actualizar el estado operativo ante novedades críticas y consultar indicadores de la flota.

## 2. Tecnologías

- Python
- Streamlit
- Pandas
- Supabase / PostgreSQL
- Supabase Storage

## 3. Estructura del proyecto

```text
/
├── app/
│   └── apparaya.py
├── docs/
│   ├── DER.md
│   └── informe_tecnico.md
├── sql/
│   └── README.md
├── .gitignore
├── requirements.txt
└── README.md
```

Los secretos de Supabase se mantienen fuera del repositorio en:

```text
.streamlit/secrets.toml
```

Formato:

```toml
[supabase]
url = "TU_SUPABASE_URL"
key = "TU_SUPABASE_KEY"
```

## 4. Instalación local

Crear y activar el entorno virtual:

```powershell
python -m venv venv
.env\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

Crear `.streamlit/secrets.toml` con las credenciales entregadas para el entorno de trabajo.

Ejecutar:

```powershell
streamlit run app/apparaya.py
```

## 5. Funcionalidades principales

### Administrador

- Indicadores de conductores, vehículos, autorizaciones e inspecciones.
- Promedio de combustible registrado.
- Disponibilidad global de la flota.
- Cantidad de vehículos operativos y no operativos.
- Matriz visual del estado de la flota.
- Analítica de kilometraje acumulado.
- Frecuencia de inspecciones por vehículo.
- Auditoría histórica por patente.

### Guardia de Garita

- Selección de patente.
- Consulta del vehículo.
- Consulta del conductor.
- Verificación de autorización vigente.
- Resolución de acceso:
  - AUTORIZADO
  - DENEGADO
  - ALERTA DE ESTADO

### Conductor Operativo

- Selección de vehículo y conductor autorizado.
- Registro de kilometraje.
- Nivel de combustible.
- Estado de neumáticos.
- Estado de luces.
- Observaciones.
- Evidencia fotográfica.
- Actualización automática del estado del vehículo cuando se detectan novedades críticas.

## 6. Evidencia fotográfica

La aplicación restringe las imágenes a un máximo de 800 KB antes de intentar subirlas al bucket `evidencias-vehiculares`.

Los formatos considerados son JPG y PNG.

## 7. Seguridad

Las credenciales de Supabase no forman parte del código fuente ni deben publicarse en GitHub.

El archivo `.streamlit/secrets.toml` está incluido en `.gitignore`.

El selector de perfiles implementado en esta versión corresponde a una simulación funcional para la evaluación. La autenticación real y las políticas RLS deben implementarse directamente en Supabase si el sistema se lleva a producción.

## 8. Base de datos

La aplicación trabaja con las tablas proporcionadas para la actividad:

- `conductores`
- `vehiculos`
- `autorizaciones`
- `reportes_estado`

No se requiere modificar las tablas originales para ejecutar la aplicación.

## 9. Flujo general

```text
Usuario
   |
   v
Streamlit
   |
   +---- Administrador ----> KPIs / Estado / Analítica / Auditoría
   |
   +---- Guardia ----------> Validación vehículo + conductor + autorización
   |
   +---- Conductor --------> Check-in / inspección / evidencia
                                  |
                                  v
                              Supabase
                           PostgreSQL + Storage
```
