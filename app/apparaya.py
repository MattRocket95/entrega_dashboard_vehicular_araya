import pandas as pd
import streamlit as st
from supabase import Client, create_client

st.set_page_config(
    page_title="Dashboard Operativo Vehicular",
    layout="wide",
)

@st.cache_resource
def conectar_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

try:
    supabase = conectar_supabase()
except Exception as error:
    st.error("No fue posible conectar con Supabase.")
    st.error(str(error))
    st.stop()


def cargar_tabla(nombre_tabla: str) -> pd.DataFrame:
    try:
        respuesta = supabase.table(nombre_tabla).select("*").execute()
        return pd.DataFrame(respuesta.data or [])
    except Exception as error:
        st.error(f"Error al consultar {nombre_tabla}: {error}")
        return pd.DataFrame()


def subir_evidencia(archivo, patente: str) -> str:
    if archivo is None:
        return ""

    contenido = archivo.getvalue()

    if len(contenido) > 800 * 1024:
        st.error("La evidencia fotografica supera el limite de 800 KB.")
        return ""

    try:
        extension = "jpg"
        if archivo.name.lower().endswith(".png"):
            extension = "png"

        nombre = (
            f"evidencia_{patente}_"
            f"{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}.{extension}"
        )

        (
            supabase
            .storage
            .from_("evidencias-vehiculares")
            .upload(
                nombre,
                contenido,
                file_options={"content-type": f"image/{extension}"},
            )
        )

        return (
            supabase
            .storage
            .from_("evidencias-vehiculares")
            .get_public_url(nombre)
        )

    except Exception as error:
        st.warning(
            f"No se pudo almacenar la evidencia fotografica: {error}"
        )
        return ""


def actualizar_estado_vehiculo(
    patente: str,
    presion_neumaticos: bool,
    luces_operativas: bool,
    observaciones: str,
) -> str:
    texto = str(observaciones or "").strip().lower()

    palabras_criticas = [
        "critico",
        "crítico",
        "freno",
        "frenos",
        "falla grave",
        "severo",
    ]

    es_critico = any(palabra in texto for palabra in palabras_criticas)

    if es_critico:
        nuevo_estado = "Crítico"
    elif not presion_neumaticos or not luces_operativas:
        nuevo_estado = "Requiere Mantención"
    else:
        return ""

    try:
        (
            supabase
            .table("vehiculos")
            .update({"estado_operativo": nuevo_estado})
            .eq("patente", patente)
            .execute()
        )
        return nuevo_estado
    except Exception as error:
        st.warning(
            f"El reporte fue guardado, pero no se pudo actualizar "
            f"el estado del vehiculo: {error}"
        )
        return ""


df_conductores = cargar_tabla("conductores")
df_vehiculos = cargar_tabla("vehiculos")
df_autorizaciones = cargar_tabla("autorizaciones")
df_reportes = cargar_tabla("reportes_estado")


st.title("Dashboard Operativo Vehicular")
st.write(
    "Consulta, control y seguimiento del material rodante "
    "mediante Streamlit y Supabase."
)

st.sidebar.header("Perfil de usuario")

perfil = st.sidebar.selectbox(
    "Seleccionar perfil de prueba",
    [
        "Administrador",
        "Guardia de Garita",
        "Conductor Operativo",
    ],
)

st.sidebar.write(f"Perfil activo: {perfil}")


def mostrar_indicadores():
    st.subheader("Indicadores Operacionales")

    autorizaciones_vigentes = 0

    if (
        not df_autorizaciones.empty
        and "vigente" in df_autorizaciones.columns
    ):
        autorizaciones_vigentes = int(
            df_autorizaciones["vigente"].fillna(False).sum()
        )

    if not df_reportes.empty:
        combustible_promedio = float(
            df_reportes["nivel_combustible"].fillna(0).mean()
        )

        neumaticos_ok = int(
            df_reportes["presion_neumaticos"].fillna(False).sum()
        )

        luces_ok = int(
            df_reportes["luces_operativas"].fillna(False).sum()
        )

        inspecciones_observadas = int(
            (
                df_reportes["observaciones"]
                .fillna("")
                .astype(str)
                .str.strip()
                .ne("")
            ).sum()
        )
    else:
        combustible_promedio = 0
        neumaticos_ok = 0
        luces_ok = 0
        inspecciones_observadas = 0

    if (
        not df_vehiculos.empty
        and "estado_operativo" in df_vehiculos.columns
    ):
        estados = (
            df_vehiculos["estado_operativo"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        vehiculos_operativos = int(
            estados.eq("operativo").sum()
        )
    else:
        vehiculos_operativos = 0

    vehiculos_no_operativos = max(
        len(df_vehiculos) - vehiculos_operativos,
        0,
    )

    disponibilidad_flota = 0

    if len(df_vehiculos) > 0:
        disponibilidad_flota = (
            vehiculos_operativos / len(df_vehiculos)
        ) * 100

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Conductores registrados", len(df_conductores))

    with col2:
        st.metric("Vehiculos registrados", len(df_vehiculos))

    with col3:
        st.metric("Autorizaciones vigentes", autorizaciones_vigentes)

    with col4:
        st.metric("Inspecciones realizadas", len(df_reportes))

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Combustible promedio",
            f"{combustible_promedio:.1f}%",
        )

    with col2:
        st.metric(
            "Neumaticos OK",
            f"{neumaticos_ok} / {len(df_reportes)}",
        )

    with col3:
        st.metric(
            "Luces operativas",
            f"{luces_ok} / {len(df_reportes)}",
        )

    with col4:
        st.metric(
            "Inspecciones con observaciones",
            inspecciones_observadas,
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Disponibilidad global de la flota",
            f"{disponibilidad_flota:.1f}%",
        )

    with col2:
        st.metric(
            "Vehiculos operativos",
            vehiculos_operativos,
        )

    with col3:
        st.metric(
            "Vehiculos no operativos",
            vehiculos_no_operativos,
        )


def mostrar_matriz_estado():
    st.subheader("Estado de la flota")

    if df_vehiculos.empty:
        st.info("No existen vehiculos registrados.")
        return

    for inicio in range(0, len(df_vehiculos), 3):
        fila = df_vehiculos.iloc[inicio:inicio + 3]
        columnas = st.columns(3)

        for columna, (_, vehiculo) in zip(columnas, fila.iterrows()):
            estado = str(
                vehiculo.get("estado_operativo", "Sin estado")
            )

            estado_normalizado = estado.lower()

            if estado_normalizado == "operativo":
                fondo = "#d9f2df"
                borde = "#4caf50"
            elif "crit" in estado_normalizado:
                fondo = "#f8d7da"
                borde = "#dc3545"
            else:
                fondo = "#fff3cd"
                borde = "#ffc107"

            texto = (
                f"<div style='"
                f"border:1px solid {borde};"
                f"background:{fondo};"
                f"padding:12px;"
                f"border-radius:6px;"
                f"margin-bottom:10px;'>"
                f"<strong>{vehiculo.get('patente', '')}</strong><br>"
                f"{vehiculo.get('marca_modelo', '')}<br>"
                f"Estado: {estado}"
                f"</div>"
            )

            columna.markdown(texto, unsafe_allow_html=True)


def mostrar_graficos():
    st.subheader("Analitica de uso y consumo")

    if df_vehiculos.empty:
        st.info("No existen datos de vehiculos para analizar.")
        return

    col1, col2 = st.columns(2)

    datos_km = df_vehiculos[
        ["patente", "kilometraje_actual"]
    ].copy()

    datos_km["kilometraje_actual"] = pd.to_numeric(
        datos_km["kilometraje_actual"],
        errors="coerce",
    )

    datos_km = (
        datos_km
        .dropna()
        .set_index("patente")
        .sort_values("kilometraje_actual", ascending=False)
    )

    with col1:
        st.write("Kilometraje acumulado por vehiculo")
        st.bar_chart(datos_km["kilometraje_actual"])

    if not df_reportes.empty and "patente" in df_reportes.columns:
        frecuencia = (
            df_reportes
            .groupby("patente")
            .size()
            .sort_values(ascending=False)
        )
    else:
        frecuencia = pd.Series(dtype="int64")

    with col2:
        st.write("Frecuencia de inspecciones por vehiculo")

        if frecuencia.empty:
            st.info("No existen registros suficientes.")
        else:
            st.bar_chart(frecuencia)


def mostrar_feed():
    st.subheader("Registro cronologico de inspecciones")

    if df_reportes.empty:
        st.info("No existen registros de inspeccion.")
        return

    reportes_ordenados = df_reportes.copy()

    reportes_ordenados["fecha_reporte"] = pd.to_datetime(
        reportes_ordenados["fecha_reporte"],
        errors="coerce",
    )

    reportes_ordenados = reportes_ordenados.sort_values(
        "fecha_reporte",
        ascending=False,
    )

    for _, reporte in reportes_ordenados.iterrows():
        fecha = reporte["fecha_reporte"]

        if pd.notna(fecha):
            fecha_formateada = fecha.strftime("%d-%m-%Y %H:%M")
        else:
            fecha_formateada = "Fecha no disponible"

        patente = str(
            reporte.get("patente", "No disponible")
        )

        st.markdown("---")

        col_info, col_img = st.columns([2, 1])

        with col_info:
            st.write(f"Fecha y hora: {fecha_formateada}")
            st.write(f"Patente: {patente}")
            st.write(
                f"Conductor: "
                f"{reporte.get('rut_conductor', 'No disponible')}"
            )
            st.write(
                f"Kilometraje: "
                f"{reporte.get('kilometraje_salida', 'No disponible')} km"
            )
            st.write(
                f"Combustible: "
                f"{reporte.get('nivel_combustible', 'No disponible')}%"
            )

            presion = bool(
                reporte.get("presion_neumaticos", False)
            )

            luces = bool(
                reporte.get("luces_operativas", False)
            )

            st.write(
                f"Presion de neumaticos: "
                f"{'OK' if presion else 'Revisar'}"
            )

            st.write(
                f"Luces operativas: "
                f"{'OK' if luces else 'Revisar'}"
            )

            observaciones = reporte.get("observaciones", "")

            if (
                pd.notna(observaciones)
                and str(observaciones).strip()
            ):
                st.write(
                    f"Observaciones: {observaciones}"
                )

        with col_img:
            foto_url = reporte.get(
                "foto_evidencia_url",
                "",
            )

            if (
                pd.notna(foto_url)
                and str(foto_url).strip()
            ):
                st.image(
                    foto_url,
                    width=220,
                    caption="Evidencia fotografica",
                )
            else:
                st.info("Sin evidencia fotografica")


def mostrar_guardia():
    st.header("Control de Acceso Vehicular")

    if df_vehiculos.empty or df_conductores.empty:
        st.warning("No existen datos maestros suficientes.")
        return

    patentes = sorted(
        df_vehiculos["patente"]
        .dropna()
        .astype(str)
        .tolist()
    )

    patente = st.selectbox(
        "Patente del vehiculo",
        patentes,
    )

    vehiculo = df_vehiculos.loc[
        df_vehiculos["patente"].astype(str) == patente
    ].iloc[0]

    st.write(
        f"Vehiculo: {vehiculo.get('marca_modelo', 'No disponible')}"
    )

    st.write(
        f"Estado operativo: "
        f"{vehiculo.get('estado_operativo', 'No disponible')}"
    )

    autorizaciones_validas = df_autorizaciones.loc[
        (df_autorizaciones["patente"].astype(str) == patente)
        & (df_autorizaciones["vigente"] == True)
    ]

    conductores_validos = df_conductores.loc[
        (
            df_conductores["rut"].isin(
                autorizaciones_validas["rut_conductor"]
            )
        )
        & (
            df_conductores["estado"].astype(str).str.lower()
            == "activo"
        )
    ].copy()

    if conductores_validos.empty:
        st.error(
            "DENEGADO: no existe un conductor activo "
            "con autorizacion vigente para esta patente."
        )
        return

    opciones = {
        f"{fila['rut']} - {fila['nombre_completo']}": fila["rut"]
        for _, fila in conductores_validos.iterrows()
    }

    conductor = st.selectbox(
        "Conductor",
        list(opciones.keys()),
    )

    estado = str(
        vehiculo.get("estado_operativo", "")
    ).strip().lower()

    if "crit" in estado:
        st.error(
            "ALERTA DE ESTADO: el vehiculo se encuentra en estado critico."
        )
    elif estado != "operativo":
        st.warning(
            "ALERTA DE ESTADO: el vehiculo requiere mantencion."
        )
    else:
        st.success(
            "AUTORIZADO: vehiculo y conductor cuentan "
            "con habilitacion vigente."
        )

    st.write(f"Conductor seleccionado: {conductor}")


def mostrar_formulario_conductor():
    st.header("Check-in Operativo del Conductor")

    if df_vehiculos.empty or df_conductores.empty:
        st.warning("No existen datos maestros suficientes.")
        return

    patentes = sorted(
        df_vehiculos["patente"]
        .dropna()
        .astype(str)
        .tolist()
    )

    patente = st.selectbox(
        "Vehiculo",
        patentes,
        key="conductor_patente",
    )

    vehiculo = df_vehiculos.loc[
        df_vehiculos["patente"].astype(str) == patente
    ].iloc[0]

    st.write(
        f"Tipo de vehiculo: "
        f"{vehiculo.get('tipo_vehiculo', 'No disponible')}"
    )
    st.write(
        f"Marca y modelo: "
        f"{vehiculo.get('marca_modelo', 'No disponible')}"
    )
    st.write(
        f"Kilometraje actual: "
        f"{vehiculo.get('kilometraje_actual', 'No disponible')} km"
    )
    st.write(
        f"Estado operativo: "
        f"{vehiculo.get('estado_operativo', 'No disponible')}"
    )

    conductores = df_conductores.loc[
        df_conductores["estado"].astype(str).str.lower() == "activo"
    ].copy()

    if conductores.empty:
        st.warning("No existen conductores activos.")
        return

    opciones = {
        f"{fila['rut']} - {fila['nombre_completo']}": fila["rut"]
        for _, fila in conductores.iterrows()
    }

    conductor_nombre = st.selectbox(
        "Conductor",
        list(opciones.keys()),
        key="conductor_nombre",
    )

    rut_conductor = opciones[conductor_nombre]

    with st.form("formulario_checkin"):
        st.subheader("Parametros de inspeccion")

        col1, col2, col3 = st.columns(3)

        with col1:
            kilometraje_salida = st.number_input(
                "Kilometraje de salida",
                min_value=0,
                step=1,
                value=int(
                    vehiculo.get("kilometraje_actual", 0) or 0
                ),
            )

        with col2:
            nivel_combustible = st.number_input(
                "Nivel de combustible (%)",
                min_value=0,
                max_value=100,
                step=1,
                value=50,
            )

        with col3:
            presion_neumaticos = st.selectbox(
                "Presion de neumaticos",
                ["OK", "Revisar"],
                key="checkin_presion",
            )

        luces_operativas = st.selectbox(
            "Luces operativas",
            ["OK", "Revisar"],
            key="checkin_luces",
        )

        observaciones = st.text_area(
            "Observaciones",
            placeholder=(
                "Ingrese novedades, daños, advertencias "
                "u otras observaciones."
            ),
        )

        foto = st.file_uploader(
            "Evidencia fotografica",
            type=["jpg", "jpeg", "png"],
        )

        guardar = st.form_submit_button(
            "Guardar inspeccion"
        )

        if guardar:
            presion_ok = presion_neumaticos == "OK"
            luces_ok = luces_operativas == "OK"

            foto_url = subir_evidencia(
                foto,
                patente,
            )

            registro = {
                "patente": patente,
                "rut_conductor": rut_conductor,
                "kilometraje_salida": kilometraje_salida,
                "nivel_combustible": nivel_combustible,
                "presion_neumaticos": presion_ok,
                "luces_operativas": luces_ok,
                "observaciones": observaciones,
                "foto_evidencia_url": foto_url,
            }

            try:
                (
                    supabase
                    .table("reportes_estado")
                    .insert(registro)
                    .execute()
                )

                nuevo_estado = actualizar_estado_vehiculo(
                    patente,
                    presion_ok,
                    luces_ok,
                    observaciones,
                )

                st.success(
                    "Inspeccion registrada correctamente."
                )

                if nuevo_estado:
                    st.warning(
                        f"El vehiculo fue actualizado a: "
                        f"{nuevo_estado}"
                    )

                st.info(
                    "El registro fue almacenado en Supabase."
                )

            except Exception as error:
                st.error(
                    f"No fue posible guardar la inspeccion: {error}"
                )


def mostrar_auditoria():
    st.header("Auditoria de Incidencias")

    if df_reportes.empty:
        st.info("No existen reportes de estado.")
        return

    patentes = sorted(
        df_reportes["patente"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    patente = st.selectbox(
        "Seleccionar patente para auditoria",
        patentes,
        key="auditoria_patente",
    )

    reportes = df_reportes.loc[
        df_reportes["patente"].astype(str) == patente
    ].copy()

    reportes["fecha_reporte"] = pd.to_datetime(
        reportes["fecha_reporte"],
        errors="coerce",
    )

    reportes = reportes.sort_values(
        "fecha_reporte",
        ascending=False,
    )

    st.write(
        f"Cantidad de reportes: {len(reportes)}"
    )

    for _, reporte in reportes.iterrows():
        fecha = reporte["fecha_reporte"]

        if pd.notna(fecha):
            fecha = fecha.strftime("%d-%m-%Y %H:%M")
        else:
            fecha = "Fecha no disponible"

        st.markdown("---")
        st.write(f"Fecha: {fecha}")
        st.write(
            f"Conductor: "
            f"{reporte.get('rut_conductor', 'No disponible')}"
        )
        st.write(
            f"Kilometraje: "
            f"{reporte.get('kilometraje_salida', 'No disponible')} km"
        )
        st.write(
            f"Combustible: "
            f"{reporte.get('nivel_combustible', 'No disponible')}%"
        )
        st.write(
            f"Neumaticos: "
            f"{'OK' if reporte.get('presion_neumaticos', False) else 'Revisar'}"
        )
        st.write(
            f"Luces: "
            f"{'OK' if reporte.get('luces_operativas', False) else 'Revisar'}"
        )

        observaciones = str(
            reporte.get("observaciones", "") or ""
        ).strip()

        if observaciones:
            st.write(f"Observaciones: {observaciones}")

        foto_url = str(
            reporte.get("foto_evidencia_url", "") or ""
        ).strip()

        if foto_url:
            st.image(
                foto_url,
                width=350,
                caption="Evidencia fotografica",
            )
        else:
            st.info("Este reporte no tiene evidencia fotografica.")


def mostrar_tablas():
    st.header("Informacion de la base de datos")

    (
        tab_conductores,
        tab_vehiculos,
        tab_autorizaciones,
        tab_reportes,
    ) = st.tabs(
        [
            "Conductores",
            "Vehiculos",
            "Autorizaciones",
            "Reportes de estado",
        ]
    )

    with tab_conductores:
        st.dataframe(
            df_conductores,
            use_container_width=True,
            hide_index=True,
        )

    with tab_vehiculos:
        st.dataframe(
            df_vehiculos,
            use_container_width=True,
            hide_index=True,
        )

    with tab_autorizaciones:
        st.dataframe(
            df_autorizaciones,
            use_container_width=True,
            hide_index=True,
        )

    with tab_reportes:
        st.dataframe(
            df_reportes,
            use_container_width=True,
            hide_index=True,
        )


if perfil == "Administrador":
    mostrar_indicadores()
    st.divider()
    mostrar_matriz_estado()
    st.divider()
    mostrar_graficos()
    st.divider()
    mostrar_auditoria()
    st.divider()
    mostrar_feed()
    st.divider()
    mostrar_tablas()

elif perfil == "Guardia de Garita":
    mostrar_guardia()

elif perfil == "Conductor Operativo":
    mostrar_formulario_conductor()

st.divider()

st.caption(
    "Morir como héroe o vivir lo suficiente para convertirse en villano"
)
