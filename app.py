import io
import cloudpickle
import pandas as pd
import streamlit as st
import plotly.express as px


# CONFIGURACIÓN

st.set_page_config(
    page_title="Grupo GEE - Licitaciones",
    page_icon="📊",
    layout="wide",
)

# Apariencia: solo presentación; no cambia los datos.
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,0.22);
        border-radius: 12px;
        padding: 12px 16px;
        background: rgba(128,128,128,0.04);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# CARGA DEL MOTOR

@st.cache_resource
def cargar_motor():
    with open("motor_licitaciones_final.pkl", "rb") as f:
        return cloudpickle.load(f)


try:
    motor = cargar_motor()
except Exception as e:
    st.error("No se ha podido cargar el motor de licitaciones.")
    st.exception(e)
    st.stop()


# CARGA DEL DASHBOARD

@st.cache_data(show_spinner=False)
def cargar_dashboard():
    return pd.read_csv(
        "dashboard_servicios_final.csv",
        encoding="utf-8-sig",
    )


@st.cache_data(show_spinner=False)
def procesar_excel(contenido_archivo):
    df_entrada = pd.read_excel(io.BytesIO(contenido_archivo))

    # Preparación del presupuesto exactamente como en NB6.
    if "Presupuesto base sin impuestos" not in df_entrada.columns:
        raise ValueError(
            "Falta la columna 'Presupuesto base sin impuestos' "
            "en el Excel de entrada."
        )

    df_entrada["Presupuesto base sin impuestos oportunidad"] = (
        pd.to_numeric(
            df_entrada["Presupuesto base sin impuestos"],
            errors="coerce"
        )
    )

    df_entrada["presupuesto_oportunidad"] = (
        df_entrada["Presupuesto base sin impuestos oportunidad"]
    )

    df_entrada["presupuesto_total"] = (
        df_entrada["Presupuesto base sin impuestos oportunidad"]
    )

    return motor.predict(df_entrada)


# CABECERA Y NAVEGACIÓN

st.title("Grupo GEE")
st.write("Análisis histórico y evaluación de oportunidades de licitación.")

modo = st.radio(
    "Selecciona una opción",
    ["🎯 Motor de licitaciones", "📊 Dashboard histórico"],
    horizontal=True,
)


# DASHBOARD

if modo == "📊 Dashboard histórico":

    st.title("Dashboard histórico de licitaciones")
    st.caption(
        "Mercado histórico de servicios de mantenimiento de equipamiento electromédico."
    )

    try:
        df_dash = cargar_dashboard().copy()
    except Exception as e:
        st.error("No se ha podido cargar el dataset del dashboard.")
        st.exception(e)
        st.stop()

    columnas_requeridas = [
        "Número de expediente",
        "anio_publicacion",
        "mes_publicacion",
        "comunidad_autonoma",
        "tipo_organo",
        "procedimiento_agrupado",
        "presupuesto_expediente",
        "ganador_grupo",
        "gano_gee",
        "resultado_agrupado",
    ]

    faltantes = [c for c in columnas_requeridas if c not in df_dash.columns]
    if faltantes:
        st.error("Faltan columnas necesarias en dashboard_servicios_final.csv:")
        st.write(faltantes)
        st.stop()

    for col in ["anio_publicacion", "mes_publicacion", "duracion_meses", "presupuesto_expediente"]:
        if col in df_dash.columns:
            df_dash[col] = pd.to_numeric(df_dash[col], errors="coerce")

    df_dash["gano_gee"] = df_dash["gano_gee"].fillna(False).astype(bool)

    # FILTROS

    st.sidebar.header("Filtros")

    anios = sorted(
        df_dash["anio_publicacion"].dropna().astype(int).unique().tolist()
    )
    anios_sel = st.sidebar.multiselect(
        "Año de publicación",
        anios,
        default=anios,
    )

    ccaas = sorted(
        df_dash["comunidad_autonoma"].dropna().astype(str).unique().tolist()
    )
    ccaas_sel = st.sidebar.multiselect(
        "Comunidad autónoma",
        ccaas,
        default=ccaas,
    )

    competidores = (
        df_dash["ganador_grupo"]
        .fillna("Sin información")
        .astype(str)
        .value_counts()
        .index
        .tolist()
    )
    competidores_sel = st.sidebar.multiselect(
        "Competidores",
        competidores,
        default=competidores,
    )

    organos = sorted(
        df_dash["tipo_organo"].dropna().astype(str).unique().tolist()
    )
    organos_sel = st.sidebar.multiselect(
        "Tipo de órgano",
        organos,
        default=organos,
    )

    procedimientos = sorted(
        df_dash["procedimiento_agrupado"].dropna().astype(str).unique().tolist()
    )
    procedimientos_sel = st.sidebar.multiselect(
        "Procedimiento",
        procedimientos,
        default=procedimientos,
    )

    # APLICAR FILTROS

    df_filtrado = df_dash.copy()

    if anios_sel:
        df_filtrado = df_filtrado[
            df_filtrado["anio_publicacion"].isin(anios_sel)
        ]

    if ccaas_sel:
        df_filtrado = df_filtrado[
            df_filtrado["comunidad_autonoma"].isin(ccaas_sel)
        ]

    if competidores_sel:
        df_filtrado = df_filtrado[
            df_filtrado["ganador_grupo"]
            .fillna("Sin información")
            .astype(str)
            .isin(competidores_sel)
        ]

    if organos_sel:
        df_filtrado = df_filtrado[
            df_filtrado["tipo_organo"].isin(organos_sel)
        ]

    if procedimientos_sel:
        df_filtrado = df_filtrado[
            df_filtrado["procedimiento_agrupado"].isin(procedimientos_sel)
        ]

    if df_filtrado.empty:
        st.warning("No hay expedientes que cumplan los filtros seleccionados.")
        st.stop()

    # KPIs

    total = len(df_filtrado)
    presupuesto_total = df_filtrado["presupuesto_expediente"].sum()
    presupuesto_mediano = df_filtrado["presupuesto_expediente"].median()
    gee = int(df_filtrado["gano_gee"].sum())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Expedientes", f"{total:,}")
    with c2:
        st.metric("Mercado analizado", f"{presupuesto_total / 1_000_000:.1f} M€")
    with c3:
        st.metric("Presupuesto mediano", f"{presupuesto_mediano:,.0f} €")
    with c4:
        st.metric("Expedientes GEE", f"{gee:,}")

    st.divider()

    # PALETA VISUAL: cambia el ESTILO, no el contenido.
    palette = px.colors.qualitative.Safe

    # 1. EVOLUCIÓN ANUAL — MISMO DATO, ESTILO MEJORADO

    st.subheader("Evolución del mercado")

    anual = (
        df_filtrado.dropna(subset=["anio_publicacion"])
        .groupby("anio_publicacion")
        .size()
        .reset_index(name="expedientes")
        .sort_values("anio_publicacion")
    )
    anual["anio_publicacion"] = anual["anio_publicacion"].astype(int)

    fig = px.line(
        anual,
        x="anio_publicacion",
        y="expedientes",
        markers=True,
        title="Expedientes publicados por año",
        labels={"anio_publicacion": "Año", "expedientes": "Expedientes"},
    )
    fig.update_traces(
        line=dict(width=3, color=palette[0]),
        marker=dict(size=9, color=palette[1]),
        hovertemplate="Año %{x}<br>Expedientes %{y:,}<extra></extra>",
    )
    fig.update_layout(
        height=390,
        margin=dict(l=25, r=25, t=60, b=25),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # 2. ESTACIONALIDAD — MISMO DATO, BARRAS VERTICALES ESTILIZADAS

    st.subheader("Estacionalidad")

    meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    mensual = (
        df_filtrado.dropna(subset=["mes_publicacion"])
        .groupby("mes_publicacion")
        .size()
        .reindex(range(1, 13), fill_value=0)
        .reset_index(name="expedientes")
    )
    mensual["mes"] = mensual["mes_publicacion"].astype(int).map(
        dict(enumerate(meses, start=1))
    )

    fig = px.bar(
        mensual,
        x="mes",
        y="expedientes",
        text="expedientes",
        title="Expedientes publicados por mes",
        labels={"mes": "Mes", "expedientes": "Expedientes"},
        color="expedientes",
        color_continuous_scale="Viridis",
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="%{x}<br>Expedientes %{y:,}<extra></extra>",
    )
    fig.update_layout(
        height=400,
        margin=dict(l=25, r=25, t=60, b=25),
        coloraxis_showscale=False,
        xaxis=dict(categoryorder="array", categoryarray=meses),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # 3. PROCEDIMIENTO + RESULTADO — MISMO CONTENIDO, DONUTS

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Procedimiento de contratación")
        proc = (
            df_filtrado["procedimiento_agrupado"]
            .fillna("Sin información")
            .value_counts()
            .reset_index()
        )
        proc.columns = ["procedimiento", "expedientes"]
        fig = px.pie(
            proc,
            names="procedimiento",
            values="expedientes",
            hole=0.58,
            title="Distribución por procedimiento",
            color_discrete_sequence=palette,
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate="%{label}<br>Expedientes %{value:,}<br>%{percent}<extra></extra>",
        )
        fig.update_layout(height=430, margin=dict(l=20, r=20, t=60, b=20))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.subheader("Resultado de las licitaciones")
        resultados = (
            df_filtrado["resultado_agrupado"]
            .fillna("Sin resultado")
            .value_counts()
            .reset_index()
        )
        resultados.columns = ["resultado", "expedientes"]
        fig = px.pie(
            resultados,
            names="resultado",
            values="expedientes",
            hole=0.58,
            title="Distribución por resultado",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent",
            hovertemplate="%{label}<br>Expedientes %{value:,}<br>%{percent}<extra></extra>",
        )
        fig.update_layout(height=430, margin=dict(l=20, r=20, t=60, b=20))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # 4. CCAA — MISMO CONTENIDO, BARRA HORIZONTAL CON PALETA

    st.subheader("Distribución territorial")

    ccaa = (
        df_filtrado["comunidad_autonoma"]
        .fillna("Sin información")
        .value_counts()
        .sort_values(ascending=True)
        .reset_index()
    )
    ccaa.columns = ["comunidad_autonoma", "expedientes"]

    fig = px.bar(
        ccaa,
        x="expedientes",
        y="comunidad_autonoma",
        orientation="h",
        text="expedientes",
        title="Expedientes por comunidad autónoma",
        labels={
            "expedientes": "Expedientes",
            "comunidad_autonoma": "Comunidad autónoma",
        },
        color="expedientes",
        color_continuous_scale="Tealgrn",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=540,
        margin=dict(l=20, r=55, t=60, b=25),
        coloraxis_showscale=False,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # 5. COMPETENCIA — MISMO CONTENIDO, BARRA HORIZONTAL ESTILIZADA

    st.subheader("Competencia")

    competencia = (
        df_filtrado["ganador_grupo"]
        .fillna("Sin información")
        .value_counts()
        .sort_values(ascending=True)
        .reset_index()
    )
    competencia.columns = ["competidor", "expedientes"]

    fig = px.bar(
        competencia,
        x="expedientes",
        y="competidor",
        orientation="h",
        text="expedientes",
        title="Adjudicaciones por competidor",
        labels={"expedientes": "Expedientes", "competidor": "Competidor"},
        color="expedientes",
        color_continuous_scale="Sunsetdark",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=max(460, 38 * len(competencia)),
        margin=dict(l=20, r=60, t=60, b=25),
        coloraxis_showscale=False,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # 6. GEE POR AÑO — MISMO CONTENIDO, LÍNEA

    st.subheader("Posición de Grupo GEE")

    gee_anual = (
        df_filtrado.dropna(subset=["anio_publicacion"])
        .groupby("anio_publicacion")
        .agg(
            expedientes=("Número de expediente", "nunique"),
            expedientes_gee=("gano_gee", "sum"),
        )
        .reset_index()
        .sort_values("anio_publicacion")
    )
    gee_anual["cuota_gee"] = (
        gee_anual["expedientes_gee"] / gee_anual["expedientes"] * 100
    )
    gee_anual["anio_publicacion"] = gee_anual["anio_publicacion"].astype(int)

    fig = px.line(
        gee_anual,
        x="anio_publicacion",
        y="cuota_gee",
        markers=True,
        title="Cuota GEE por año",
        labels={
            "anio_publicacion": "Año",
            "cuota_gee": "Cuota GEE (%)",
        },
    )
    fig.update_traces(
        line=dict(width=3, color=palette[3]),
        marker=dict(size=9, color=palette[4]),
        hovertemplate="Año %{x}<br>Cuota GEE %{y:.2f}%<extra></extra>",
    )
    fig.update_layout(
        height=390,
        margin=dict(l=25, r=25, t=60, b=25),
        yaxis_ticksuffix="%",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # 7. CUOTA GEE POR PROCEDIMIENTO — MISMO CONTENIDO

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Cuota GEE por procedimiento")
        gee_proc = (
            df_filtrado.groupby("procedimiento_agrupado")
            .agg(
                expedientes=("Número de expediente", "nunique"),
                expedientes_gee=("gano_gee", "sum"),
            )
            .reset_index()
        )
        gee_proc["cuota_gee"] = (
            gee_proc["expedientes_gee"] / gee_proc["expedientes"] * 100
        )
        gee_proc = gee_proc.sort_values("cuota_gee", ascending=True)

        fig = px.bar(
            gee_proc,
            x="cuota_gee",
            y="procedimiento_agrupado",
            orientation="h",
            text="cuota_gee",
            title="Cuota GEE por procedimiento",
            labels={
                "cuota_gee": "Cuota GEE (%)",
                "procedimiento_agrupado": "Procedimiento",
            },
            color="cuota_gee",
            color_continuous_scale="Blues",
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
        )
        fig.update_layout(
            height=430,
            margin=dict(l=20, r=55, t=60, b=25),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        st.subheader("Cuota GEE por comunidad autónoma")
        gee_ccaa = (
            df_filtrado.groupby("comunidad_autonoma")
            .agg(
                expedientes=("Número de expediente", "nunique"),
                expedientes_gee=("gano_gee", "sum"),
            )
            .reset_index()
        )
        gee_ccaa["cuota_gee"] = (
            gee_ccaa["expedientes_gee"] / gee_ccaa["expedientes"] * 100
        )
        gee_ccaa = gee_ccaa.sort_values("cuota_gee", ascending=True)

        fig = px.bar(
            gee_ccaa,
            x="cuota_gee",
            y="comunidad_autonoma",
            orientation="h",
            text="cuota_gee",
            title="Cuota GEE por comunidad autónoma",
            labels={
                "cuota_gee": "Cuota GEE (%)",
                "comunidad_autonoma": "Comunidad autónoma",
            },
            color="cuota_gee",
            color_continuous_scale="Aggrnyl",
        )
        fig.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
        )
        fig.update_layout(
            height=max(480, 34 * len(gee_ccaa)),
            margin=dict(l=20, r=55, t=60, b=25),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # 8. TIPO DE ÓRGANO — MISMO CONTENIDO

    st.subheader("Tipo de órgano de contratación")

    organos_df = (
        df_filtrado["tipo_organo"]
        .fillna("Sin información")
        .value_counts()
        .head(12)
        .sort_values(ascending=True)
        .reset_index()
    )
    organos_df.columns = ["tipo_organo", "expedientes"]

    fig = px.bar(
        organos_df,
        x="expedientes",
        y="tipo_organo",
        orientation="h",
        text="expedientes",
        title="Principales tipos de órgano",
        labels={
            "expedientes": "Expedientes",
            "tipo_organo": "Tipo de órgano",
        },
        color="expedientes",
        color_continuous_scale="Cividis",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=max(430, 38 * len(organos_df)),
        margin=dict(l=20, r=55, t=60, b=25),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # DATOS / DESCARGA

    with st.expander("Consultar datos del dashboard"):
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True,
        )

        csv_dashboard = df_filtrado.to_csv(
            index=False,
            encoding="utf-8-sig",
        )

        st.download_button(
            "Descargar datos filtrados (CSV)",
            data=csv_dashboard,
            file_name="dashboard_licitaciones_filtrado.csv",
            mime="text/csv",
            key="dashboard_download_csv",
        )


# MOTOR DE LICITACIONES

else:

    st.title("Motor de Licitaciones GEE")
    st.write(
        "Analiza oportunidades de licitación y obtiene un ranking automático de participación."
    )

    st.header("1. Cargar licitaciones")

    archivo = st.file_uploader(
        "Sube el Excel de licitaciones",
        type=["xlsx", "xls"],
        key="motor_file_uploader",
    )

    if archivo is not None:

        try:
            with st.spinner("Procesando licitaciones..."):
                df_resultado = procesar_excel(archivo.getvalue())

            st.success(
                f"Procesamiento completado: {len(df_resultado):,} oportunidades válidas."
            )

        except Exception as e:
            st.error("No se ha podido procesar el archivo.")
            st.exception(e)
            st.stop()

        # RESUMEN AUTOMÁTICO

        st.header("2. Resultado automático")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Oportunidades",
                f"{len(df_resultado):,}"
            )

        with col2:
            st.metric(
                "Score automático medio",
                f"{df_resultado['score_automatico_100'].mean():.2f}"
            )

        with col3:
            st.metric(
                "Score automático máximo",
                f"{df_resultado['score_automatico_100'].max():.2f}"
            )

        with col4:
            st.metric(
                "Oportunidades Alta",
                int((df_resultado["prioridad"] == "Alta").sum())
            )

        # RANKING

        st.header("3. Ranking de oportunidades")

        columnas_ranking = [
            "Número de expediente",
            "Órgano de Contratación",
            "Objeto",
            "Estado",
            "presupuesto_total",
            "duracion_meses",
            "ha_trabajado_con_grupo_gee",
            "CPV_504_principal",
            "score_ml",
            "ajuste_presupuesto",
            "ajuste_duracion",
            "bonus_grupo_gee",
            "ajuste_cpv_504",
            "ajuste_total_negocio",
            "score_automatico",
            "score_automatico_100",
            "prioridad",
        ]

        columnas_ranking = [
            col for col in columnas_ranking
            if col in df_resultado.columns
        ]

        if "score_automatico_100" not in columnas_ranking:
            st.error(
                "El motor no ha devuelto 'score_automatico_100'. "
                "El PKL no es compatible con la aplicación."
            )
            st.stop()

        ranking = (
            df_resultado[columnas_ranking]
            .sort_values("score_automatico_100", ascending=False)
            .reset_index(drop=True)
            .copy()
        )

        ranking.insert(
            0,
            "Ranking",
            range(1, len(ranking) + 1)
        )

        st.dataframe(
            ranking,
            use_container_width=True,
            hide_index=True,
        )

        # DESCARGA DEL RANKING

        csv_ranking = ranking.to_csv(
            index=False,
            encoding="utf-8-sig",
        )

        st.download_button(
            "Descargar ranking (CSV)",
            data=csv_ranking,
            file_name="ranking_licitaciones_gee.csv",
            mime="text/csv",
            key="motor_download_csv",
        )

        # EVALUACIÓN MANUAL

        st.header("4. Evaluación manual opcional")

        realizar_manual = st.checkbox(
            "Quiero realizar una evaluación manual",
            value=False,
            key="evaluacion_manual_checkbox",
        )

        if not realizar_manual:

            st.info(
                "La evaluación manual es opcional. "
                "El ranking automático mostrado arriba es el resultado principal."
            )

        else:

            st.subheader("Selecciona una oportunidad")

            columnas_selector = [
                "Número de expediente",
                "Órgano de Contratación",
                "Objeto",
                "score_automatico_100",
                "presupuesto_total",
                "duracion_meses",
            ]

            columnas_selector = [
                col for col in columnas_selector
                if col in df_resultado.columns
            ]

            columnas_obligatorias_selector = [
                "Número de expediente",
                "score_automatico_100",
            ]

            faltan_selector = [
                col for col in columnas_obligatorias_selector
                if col not in df_resultado.columns
            ]

            if faltan_selector:
                st.error(
                    "Faltan columnas necesarias para seleccionar "
                    "la oportunidad: "
                    + ", ".join(faltan_selector)
                )
                st.stop()

            df_selector = (
                df_resultado[columnas_selector]
                .sort_values(
                    "score_automatico_100",
                    ascending=False
                )
                .reset_index(drop=True)
            )

            opciones = []
            expediente_por_etiqueta = {}

            for _, fila_selector in df_selector.iterrows():

                expediente = str(
                    fila_selector["Número de expediente"]
                )

                cliente = str(
                    fila_selector["Órgano de Contratación"]
                ) if "Órgano de Contratación" in fila_selector.index else ""

                score = float(
                    fila_selector["score_automatico_100"]
                )

                etiqueta = (
                    f"{score:.2f} | "
                    f"{expediente} | "
                    f"{cliente}"
                )

                opciones.append(etiqueta)
                expediente_por_etiqueta[etiqueta] = expediente

            seleccion = st.selectbox(
                "Licitación",
                opciones,
                key="licitacion_manual_selector",
            )

            expediente_seleccionado = (
                expediente_por_etiqueta[seleccion]
            )

            fila_seleccionada = df_resultado[
                df_resultado["Número de expediente"]
                .astype(str)
                .str.strip()
                .eq(
                    expediente_seleccionado.strip()
                )
            ]

            if len(fila_seleccionada) != 1:
                st.error(
                    "No se ha podido identificar de forma única "
                    "la oportunidad."
                )
                st.stop()

            fila = fila_seleccionada.iloc[0]

            st.subheader("Información de la oportunidad")

            st.write(
                f"**Número de expediente:** "
                f"{fila['Número de expediente']}"
            )

            if "Órgano de Contratación" in fila.index:
                st.write(
                    f"**Cliente:** "
                    f"{fila['Órgano de Contratación']}"
                )

            if "Objeto" in fila.index:
                st.write(
                    f"**Objeto:** "
                    f"{fila['Objeto']}"
                )

            st.write(
                f"**Score automático:** "
                f"{fila['score_automatico_100']:.2f}"
            )

            st.write(
                f"**Presupuesto total:** "
                f"{fila['presupuesto_total']:,.2f} €"
            )

            st.write(
                f"**Duración del contrato:** "
                f"{fila['duracion_meses']:.2f} meses"
            )

            st.subheader("Datos manuales")

            col1, col2, col3 = st.columns(3)

            with col1:
                tecnicos = st.number_input(
                    "Técnicos",
                    min_value=0,
                    value=0,
                    step=1,
                    key="manual_tecnicos",
                )

            with col2:
                vehiculos = st.number_input(
                    "Vehículos",
                    min_value=0,
                    value=0,
                    step=1,
                    key="manual_vehiculos",
                )

            with col3:
                responsables = st.number_input(
                    "Responsables",
                    min_value=0,
                    value=0,
                    step=1,
                    key="manual_responsables",
                )

            estrategica = st.checkbox(
                "Es estratégica para Grupo GEE",
                value=False,
                key="manual_estrategica",
            )

            calcular = st.button(
                "Calcular score manual",
                type="primary",
                key="calcular_score_manual",
            )

            if calcular:

                try:
                    resultado_manual = motor.evaluar_manual(
                        df_resultado,
                        expediente=expediente_seleccionado,
                        realizar_evaluacion=True,
                        tecnicos=int(tecnicos),
                        vehiculos=int(vehiculos),
                        responsables=int(responsables),
                        estrategica=estrategica,
                    )

                except Exception as e:
                    st.error(
                        "No se ha podido calcular el score manual."
                    )
                    st.exception(e)
                    st.stop()

                st.divider()

                st.subheader(
                    "Resultado de la evaluación manual"
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Score automático",
                        f"{resultado_manual['score_automatico']:.2f}"
                    )

                with col2:
                    st.metric(
                        "Score manual",
                        f"{resultado_manual['score_manual']:.2f}"
                    )

                with col3:
                    st.metric(
                        "Variación",
                        f"{resultado_manual['variacion']:+.2f}"
                    )

                st.write("### Cálculo económico")

                datos_economicos = pd.DataFrame(
                    {
                        "Concepto": [
                            "Presupuesto total",
                            "Duración del contrato",
                            "Coste técnicos",
                            "Coste vehículos",
                            "Coste responsables",
                            "Coste total recursos",
                            "Margen económico",
                            "Margen relativo",
                            "Ajuste económico manual",
                        ],
                        "Valor": [
                            resultado_manual["presupuesto_total"],
                            resultado_manual["duracion_meses"],
                            resultado_manual["coste_tecnicos"],
                            resultado_manual["coste_vehiculos"],
                            resultado_manual["coste_responsables"],
                            resultado_manual["coste_total_recursos"],
                            resultado_manual["margen_economico"],
                            resultado_manual["margen_relativo"],
                            resultado_manual["ajuste_economico_manual"],
                        ],
                    }
                )

                st.dataframe(
                    datos_economicos,
                    use_container_width=True,
                    hide_index=True,
                )

                st.write("### Factor estratégico")

                st.write(
                    "Estratégica: "
                    + (
                        "Sí"
                        if resultado_manual["estrategica"]
                        else "No"
                    )
                )

                st.write(
                    f"Bonus estratégico: "
                    f"+{resultado_manual['bonus_estrategico']}"
                )

                if resultado_manual["variacion"] < 0:

                    st.warning(
                        "El score manual baja "
                        f"{abs(resultado_manual['variacion']):.2f} "
                        "puntos respecto al automático."
                    )

                elif resultado_manual["variacion"] > 0:

                    st.success(
                        "El score manual aumenta "
                        f"{resultado_manual['variacion']:.2f} "
                        "puntos respecto al automático."
                    )

                else:

                    st.info(
                        "La evaluación manual no modifica "
                        "el score automático."
                    )
