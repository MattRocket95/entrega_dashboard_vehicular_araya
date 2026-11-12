# Diagrama entidad-relación

El modelo utilizado por la aplicación se basa en las tablas proporcionadas para la actividad.

```mermaid
erDiagram
    CONDUCTORES ||--o{ AUTORIZACIONES : posee
    VEHICULOS ||--o{ AUTORIZACIONES : recibe
    CONDUCTORES ||--o{ REPORTES_ESTADO : registra
    VEHICULOS ||--o{ REPORTES_ESTADO : recibe

    CONDUCTORES {
        int id PK
        string rut UK
        string nombre_completo
        string grado_o_cargo
        string unidad_destino
        string estado
    }

    VEHICULOS {
        int id PK
        string patente UK
        string tipo_vehiculo
        string marca_modelo
        int anio
        int kilometraje_actual
        string estado_operativo
    }

    AUTORIZACIONES {
        int id PK
        string patente FK
        string rut_conductor FK
        timestamp fecha_asignacion
        boolean vigente
    }

    REPORTES_ESTADO {
        int id PK
        string patente FK
        string rut_conductor FK
        timestamp fecha_reporte
        int kilometraje_salida
        int nivel_combustible
        boolean presion_neumaticos
        boolean luces_operativas
        text observaciones
        text foto_evidencia_url
    }
```

Las columnas deben mantenerse alineadas con el esquema efectivamente disponible en el proyecto Supabase entregado para la actividad.
