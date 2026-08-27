import io
import cloudpickle
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Grupo GEE - Licitaciones",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# CARGA DEL MOTOR
# ============================================================

@st.cache_resource
def cargar_motor():

    with open(
        "motor_licitaciones_final.pkl",
        "rb"
    ) as f:

        return cloudpickle.load(f)


# ============================================================
# CARGA DEL DASHBOARD
# ============================================================

@st.cache_data(show_spinner=False)
def cargar_dashboard():

    return pd.read_csv(
        "dashboard_servicios_final.csv",
        encoding="utf-8-sig"
    )


# ============================================================
# PROCESAMIENTO DE EXCEL
# ============================================================

@st.cache_data(show_spinner=False)
def procesar_excel(
    contenido_archivo
):

    df_entrada = pd.read_excel(
        io.BytesIO(contenido_archivo)
    )

    df_resultado = motor.predict(
        df_entrada
    )

    return df_resultado


# ============================================================
# CARGAR MOTOR
# ============================================================

try:

    motor = cargar_motor()

except Exception as e:

    st.error(
        "No se ha podido cargar el motor de licitaciones."
    )

    st.exception(e)

    st.stop()


# ============================================================
# CABECERA
# ============================================================

st.title("Grupo GEE")

st.write(
    "Análisis histórico y evaluación de oportunidades "
    "de licitación."
)


# ============================================================
# NAVEGACIÓN
# ============================================================

modo = st.radio(
    "Selecciona una opción",
    [
        "📊 Dashboard histórico",
        "🎯 Motor de licitaciones"
    ],
    horizontal=True
)


# ============================================================
# ============================================================
# DASHBOARD
# ============================================================
# ============================================================

if modo == "📊 Dashboard histórico":

    st.title(
        "Dashboard histórico de licitaciones"
    )

    st.caption(
        "Mercado histórico de servicios de mantenimiento "
        "de equipamiento electromédico."
    )


    # ========================================================
    # CARGAR DATOS
    # ========================================================

    try:

        df_dash = cargar_dashboard()

    except Exception as e:

        st.error(
            "No se ha podido cargar el dataset del dashboard."
        )

        st.exception(e)

        st.stop()


    # ========================================================
    # COMPROBAR COLUMNAS
    # ========================================================

    columnas_requeridas = [
        "Número de expediente",
        "anio_publicacion",
        "mes_publicacion",
        "comunidad_autonoma",
        "tipo_organo",
        "procedimiento_agrupado",
        "presupuesto_expediente",
        "duracion_meses",
        "ganador_grupo",
        "gano_gee",
        "resultado_agrupado"
    ]

    faltantes = [
        c
        for c in columnas_requeridas
        if c not in df_dash.columns
    ]

    if faltantes:

        st.error(
            "Faltan columnas en "
            "`dashboard_servicios_final.csv`."
        )

        st.write(faltantes)

        st.stop()


    # ========================================================
    # NORMALIZACIÓN
    # ========================================================

    df_dash = df_dash.copy()

    df_dash["anio_publicacion"] = pd.to_numeric(
        df_dash["anio_publicacion"],
        errors="coerce"
    )

    df_dash["mes_publicacion"] = pd.to_numeric(
        df_dash["mes_publicacion"],
        errors="coerce"
    )

    df_dash["presupuesto_expediente"] = pd.to_numeric(
        df_dash["presupuesto_expediente"],
        errors="coerce"
    )

    df_dash["duracion_meses"] = pd.to_numeric(
        df_dash["duracion_meses"],
        errors="coerce"
    )

    df_dash["gano_gee"] = (
        df_dash["gano_gee"]
        .fillna(False)
        .astype(bool)
    )


    # ========================================================
    # SIDEBAR
    # ========================================================

    st.sidebar.header("Filtros")


    # --------------------------------------------------------
    # AÑO
    # --------------------------------------------------------

    anios_disponibles = sorted(
        df_dash[
            "anio_publicacion"
        ]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    anios_seleccionados = st.sidebar.multiselect(
        "Año de publicación",
        options=anios_disponibles,
        default=anios_disponibles
    )


    # --------------------------------------------------------
    # CCAA
    # --------------------------------------------------------

    ccaas_disponibles = sorted(
        df_dash[
            "comunidad_autonoma"
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    ccaas_seleccionadas = st.sidebar.multiselect(
        "Comunidad autónoma",
        options=ccaas_disponibles,
        default=ccaas_disponibles
    )


    # --------------------------------------------------------
    # COMPETIDORES
    # --------------------------------------------------------

    competidores_disponibles = (
        df_dash[
            "ganador_grupo"
        ]
        .fillna("Sin información")
        .astype(str)
        .value_counts()
        .index
        .tolist()
    )

    competidores_seleccionados = st.sidebar.multiselect(
        "Competidores",
        options=competidores_disponibles,
        default=competidores_disponibles
    )


    # --------------------------------------------------------
    # TIPO DE ÓRGANO
    # --------------------------------------------------------

    organos_disponibles = sorted(
        df_dash[
            "tipo_organo"
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    organos_seleccionados = st.sidebar.multiselect(
        "Tipo de órgano",
        options=organos_disponibles,
        default=organos_disponibles
    )


    # --------------------------------------------------------
    # PROCEDIMIENTO
    # --------------------------------------------------------

    procedimientos_disponibles = sorted(
        df_dash[
            "procedimiento_agrupado"
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    procedimientos_seleccionados = st.sidebar.multiselect(
        "Procedimiento",
        options=procedimientos_disponibles,
        default=procedimientos_disponibles
    )


    # ========================================================
    # APLICAR FILTROS
    # ========================================================

    df_filtrado = df_dash.copy()


    if anios_seleccionados:

        df_filtrado = df_filtrado[
            df_filtrado[
                "anio_publicacion"
            ].isin(
                anios_seleccionados
            )
        ]


    if ccaas_seleccionadas:

        df_filtrado = df_filtrado[
            df_filtrado[
                "comunidad_autonoma"
            ].isin(
                ccaas_seleccionadas
            )
        ]


    if competidores_seleccionados:

        df_filtrado = df_filtrado[
            df_filtrado[
                "ganador_grupo"
            ]
            .fillna("Sin información")
            .astype(str)
            .isin(
                competidores_seleccionados
            )
        ]


    if organos_seleccionados:

        df_filtrado = df_filtrado[
            df_filtrado[
                "tipo_organo"
            ].isin(
                organos_seleccionados
            )
        ]


    if procedimientos_seleccionados:

        df_filtrado = df_filtrado[
            df_filtrado[
                "procedimiento_agrupado"
            ].isin(
                procedimientos_seleccionados
            )
        ]


    # ========================================================
    # CONTROL
    # ========================================================

    total_expedientes = len(
        df_filtrado
    )

    if total_expedientes == 0:

        st.warning(
            "No hay expedientes que cumplan "
            "los filtros seleccionados."
        )

        st.stop()


    # ========================================================
    # KPIs
    # ========================================================

    presupuesto_total = (
        df_filtrado[
            "presupuesto_expediente"
        ]
        .sum()
    )

    presupuesto_mediano = (
        df_filtrado[
            "presupuesto_expediente"
        ]
        .median()
    )

    expedientes_gee = int(
        df_filtrado[
            "gano_gee"
        ]
        .sum()
    )

    cuota_gee = (
        expedientes_gee
        /
        total_expedientes
        *
        100
    )


    st.subheader("Resumen")


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Expedientes",
            f"{total_expedientes:,}"
        )


    with col2:

        st.metric(
            "Mercado analizado",
            f"{presupuesto_total / 1_000_000:.1f} M€"
        )


    with col3:

        st.metric(
            "Presupuesto mediano",
            f"{presupuesto_mediano:,.0f} €"
        )


    with col4:

        st.metric(
            "Cuota GEE",
            f"{cuota_gee:.2f}%"
        )


    st.divider()


    # ========================================================
    # 1. EVOLUCIÓN ANUAL — ÁREA
    # ========================================================

    st.subheader(
        "Evolución del mercado"
    )


    evolucion_anual = (
        df_filtrado
        .dropna(
            subset=[
                "anio_publicacion"
            ]
        )
        .groupby(
            "anio_publicacion"
        )
        .agg(
            expedientes=(
                "Número de expediente",
                "nunique"
            ),
            presupuesto=(
                "presupuesto_expediente",
                "sum"
            )
        )
        .reset_index()
        .sort_values(
            "anio_publicacion"
        )
    )


    evolucion_anual[
        "anio_publicacion"
    ] = (
        evolucion_anual[
            "anio_publicacion"
        ]
        .astype(int)
    )


    fig_anual = px.area(
        evolucion_anual,
        x="anio_publicacion",
        y="expedientes",
        markers=True,
        labels={
            "anio_publicacion": "Año",
            "expedientes": "Expedientes"
        },
        title="Evolución de expedientes publicados"
    )


    fig_anual.update_traces(
        line=dict(
            width=3
        ),
        marker=dict(
            size=8
        )
    )


    fig_anual.update_layout(
        height=400,
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        )
    )


    st.plotly_chart(
        fig_anual,
        use_container_width=True
    )


    # ========================================================
    # 2. ESTACIONALIDAD — HEATMAP
    # ========================================================

    st.subheader(
        "Estacionalidad de las publicaciones"
    )


    meses = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre"
    ]


    df_heatmap = (
        df_filtrado
        .dropna(
            subset=[
                "anio_publicacion",
                "mes_publicacion"
            ]
        )
        .groupby(
            [
                "anio_publicacion",
                "mes_publicacion"
            ]
        )
        .agg(
            expedientes=(
                "Número de expediente",
                "nunique"
            )
        )
        .reset_index()
    )


    df_heatmap[
        "anio_publicacion"
    ] = (
        df_heatmap[
            "anio_publicacion"
        ]
        .astype(int)
    )


    df_heatmap[
        "mes_publicacion"
    ] = (
        df_heatmap[
            "mes_publicacion"
        ]
        .astype(int)
    )


    df_heatmap[
        "mes"
    ] = (
        df_heatmap[
            "mes_publicacion"
        ]
        .map(
            dict(
                enumerate(
                    meses,
                    start=1
                )
            )
        )
    )


    pivot_heatmap = (
        df_heatmap
        .pivot(
            index="mes",
            columns="anio_publicacion",
            values="expedientes"
        )
        .reindex(meses)
    )


    fig_heatmap = px.imshow(
        pivot_heatmap,
        aspect="auto",
        labels={
            "x": "Año",
            "y": "Mes",
            "color": "Expedientes"
        },
        title="Concentración temporal de las licitaciones"
    )


    fig_heatmap.update_layout(
        height=500,
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        )
    )


    st.plotly_chart(
        fig_heatmap,
        use_container_width=True
    )


    # ========================================================
    # 3. PROCEDIMIENTO + RESULTADO — DONUTS
    # ========================================================

    col1, col2 = st.columns(2)


    with col1:

        st.subheader(
            "Procedimiento de contratación"
        )


        procedimientos = (
            df_filtrado[
                "procedimiento_agrupado"
            ]
            .fillna(
                "Sin información"
            )
            .value_counts()
            .reset_index()
        )


        procedimientos.columns = [
            "procedimiento",
            "expedientes"
        ]


        fig_procedimientos = px.pie(
            procedimientos,
            names="procedimiento",
            values="expedientes",
            hole=0.58
        )


        fig_procedimientos.update_layout(
            height=430,
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10
            ),
            legend=dict(
                orientation="h",
                y=-0.05
            )
        )


        st.plotly_chart(
            fig_procedimientos,
            use_container_width=True
        )


    with col2:

        st.subheader(
            "Resultado de las licitaciones"
        )


        resultados = (
            df_filtrado[
                "resultado_agrupado"
            ]
            .fillna(
                "Sin resultado"
            )
            .value_counts()
            .reset_index()
        )


        resultados.columns = [
            "resultado",
            "expedientes"
        ]


        fig_resultados = px.pie(
            resultados,
            names="resultado",
            values="expedientes",
            hole=0.58
        )


        fig_resultados.update_layout(
            height=430,
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10
            ),
            legend=dict(
                orientation="h",
                y=-0.05
            )
        )


        st.plotly_chart(
            fig_resultados,
            use_container_width=True
        )


    # ========================================================
    # 4. DISTRIBUCIÓN ECONÓMICA — ECDF
    # ========================================================

    st.subheader(
        "Distribución de los presupuestos"
    )


    df_presupuesto = (
        df_filtrado[
            [
                "Número de expediente",
                "presupuesto_expediente"
            ]
        ]
        .dropna()
        .copy()
    )


    df_presupuesto = df_presupuesto[
        df_presupuesto[
            "presupuesto_expediente"
        ] > 0
    ]


    if len(df_presupuesto) > 0:

        fig_ecdf = px.ecdf(
            df_presupuesto,
            x="presupuesto_expediente",
            log_x=True,
            labels={
                "presupuesto_expediente": "Presupuesto (€)",
                "y": "Proporción acumulada"
            },
            title=(
                "Distribución acumulada de los presupuestos"
            )
        )


        fig_ecdf.update_layout(
            height=450,
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20
            )
        )


        st.plotly_chart(
            fig_ecdf,
            use_container_width=True
        )


    # ========================================================
    # 5. PRESUPUESTO — BOXPLOT POR TRAMO
    # ========================================================

    st.subheader(
        "Dispersión de presupuestos"
    )


    df_box = df_filtrado[
        [
            "tramo_presupuesto",
            "presupuesto_expediente"
        ]
    ].copy()


    df_box = df_box.dropna(
        subset=[
            "tramo_presupuesto",
            "presupuesto_expediente"
        ]
    )


    if len(df_box) > 0:

        fig_box = px.box(
            df_box,
            x="tramo_presupuesto",
            y="presupuesto_expediente",
            points=False,
            labels={
                "tramo_presupuesto": "Tramo de presupuesto",
                "presupuesto_expediente": "Presupuesto (€)"
            },
            title="Distribución del presupuesto por tramo"
        )


        fig_box.update_yaxes(
            type="log"
        )


        fig_box.update_layout(
            height=480,
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=100
            )
        )


        st.plotly_chart(
            fig_box,
            use_container_width=True
        )


    # ========================================================
    # 6. PRESUPUESTO × DURACIÓN — SCATTER
    # ========================================================

    st.subheader(
        "Relación entre presupuesto y duración"
    )


    df_scatter = df_filtrado[
        [
            "Número de expediente",
            "presupuesto_expediente",
            "duracion_meses",
            "ganador_grupo",
            "gano_gee",
            "comunidad_autonoma"
        ]
    ].copy()


    df_scatter = df_scatter.dropna(
        subset=[
            "presupuesto_expediente",
            "duracion_meses"
        ]
    )


    df_scatter = df_scatter[
        (
            df_scatter[
                "presupuesto_expediente"
            ] > 0
        )
        &
        (
            df_scatter[
                "duracion_meses"
            ] >= 0
        )
    ]


    if len(df_scatter) > 0:

        limite = (
            df_scatter[
                "presupuesto_expediente"
            ]
            .quantile(
                0.98
            )
        )


        df_scatter = df_scatter[
            df_scatter[
                "presupuesto_expediente"
            ]
            <= limite
        ].copy()


        df_scatter[
            "tipo_ganador"
        ] = np.where(
            df_scatter[
                "gano_gee"
            ],
            "Grupo GEE",
            "Otros"
        )


        fig_scatter = px.scatter(
            df_scatter,
            x="duracion_meses",
            y="presupuesto_expediente",
            color="tipo_ganador",
            hover_data=[
                "Número de expediente",
                "ganador_grupo",
                "comunidad_autonoma"
            ],
            labels={
                "duracion_meses": "Duración (meses)",
                "presupuesto_expediente": "Presupuesto (€)",
                "tipo_ganador": "Ganador"
            },
            title=(
                "Presupuesto frente a duración "
                "(hasta percentil 98)"
            )
        )


        fig_scatter.update_yaxes(
            type="log"
        )


        fig_scatter.update_layout(
            height=520,
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20
            )
        )


        st.plotly_chart(
            fig_scatter,
            use_container_width=True
        )


    # ========================================================
    # 7. COMPETENCIA — ÚNICA GRÁFICA DE BARRAS
    # ========================================================

    st.subheader(
        "Competencia"
    )


    competencia = (
        df_filtrado[
            "ganador_grupo"
        ]
        .fillna(
            "Sin información"
        )
        .value_counts()
        .reset_index()
    )


    competencia.columns = [
        "competidor",
        "expedientes"
    ]


    competencia = competencia.sort_values(
        "expedientes",
        ascending=True
    )


    fig_competencia = px.bar(
        competencia,
        x="expedientes",
        y="competidor",
        orientation="h",
        text="expedientes",
        labels={
            "expedientes": "Expedientes",
            "competidor": "Competidor"
        },
        title="Adjudicaciones por competidor"
    )


    fig_competencia.update_traces(
        textposition="outside"
    )


    fig_competencia.update_layout(
        height=520,
        margin=dict(
            l=20,
            r=60,
            t=60,
            b=20
        ),
        showlegend=False
    )


    st.plotly_chart(
        fig_competencia,
        use_container_width=True
    )


    # ========================================================
    # 8. EVOLUCIÓN DE COMPETIDORES — LÍNEAS
    # ========================================================

    st.subheader(
        "Evolución de los principales competidores"
    )


    top_competidores = (
        df_filtrado[
            "ganador_grupo"
        ]
        .fillna(
            "Sin información"
        )
        .value_counts()
        .head(6)
        .index
        .tolist()
    )


    df_competidores = df_filtrado[
        df_filtrado[
            "ganador_grupo"
        ]
        .fillna(
            "Sin información"
        )
        .isin(
            top_competidores
        )
    ].copy()


    evolucion_competidores = (
        df_competidores
        .dropna(
            subset=[
                "anio_publicacion"
            ]
        )
        .groupby(
            [
                "anio_publicacion",
                "ganador_grupo"
            ]
        )
        .agg(
            expedientes=(
                "Número de expediente",
                "nunique"
            )
        )
        .reset_index()
    )


    if len(
        evolucion_competidores
    ) > 0:

        evolucion_competidores[
            "anio_publicacion"
        ] = (
            evolucion_competidores[
                "anio_publicacion"
            ]
            .astype(int)
        )


        fig_evolucion_comp = px.line(
            evolucion_competidores,
            x="anio_publicacion",
            y="expedientes",
            color="ganador_grupo",
            markers=True,
            labels={
                "anio_publicacion": "Año",
                "expedientes": "Expedientes",
                "ganador_grupo": "Competidor"
            },
            title=(
                "Evolución anual de los principales competidores"
            )
        )


        fig_evolucion_comp.update_layout(
            height=500,
            hovermode="x unified",
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20
            )
        )


        st.plotly_chart(
            fig_evolucion_comp,
            use_container_width=True
        )


    # ========================================================
    # 9. MERCADO POR CCAA — TREEMAP
    # ========================================================

    st.subheader(
        "Distribución territorial del mercado"
    )


    territorio = (
        df_filtrado
        .groupby(
            "comunidad_autonoma"
        )
        .agg(
            expedientes=(
                "Número de expediente",
                "nunique"
            ),
            presupuesto_mediano=(
                "presupuesto_expediente",
                "median"
            )
        )
        .reset_index()
    )


    if len(territorio) > 0:

        fig_territorio = px.treemap(
            territorio,
            path=[
                "comunidad_autonoma"
            ],
            values="expedientes",
            color="presupuesto_mediano",
            hover_data={
                "expedientes": True,
                "presupuesto_mediano": ":,.0f"
            },
            labels={
                "expedientes": "Expedientes",
                "presupuesto_mediano":
                    "Presupuesto mediano"
            },
            title=(
                "Peso relativo de cada comunidad autónoma"
            )
        )


        fig_territorio.update_layout(
            height=500,
            margin=dict(
                l=10,
                r=10,
                t=60,
                b=10
            )
        )


        st.plotly_chart(
            fig_territorio,
            use_container_width=True
        )


    # ========================================================
    # 10. POSICIÓN DE GEE POR CCAA — BUBBLE
    # ========================================================

    st.subheader(
        "Posición de Grupo GEE por territorio"
    )


    gee_ccaa = (
        df_filtrado
        .groupby(
            "comunidad_autonoma"
        )
        .agg(
            expedientes=(
                "Número de expediente",
                "nunique"
            ),
            expedientes_gee=(
                "gano_gee",
                "sum"
            )
        )
        .reset_index()
    )


    gee_ccaa[
        "cuota_gee"
    ] = np.where(
        gee_ccaa[
            "expedientes"
        ] > 0,
        (
            gee_ccaa[
                "expedientes_gee"
            ]
            /
            gee_ccaa[
                "expedientes"
            ]
            *
            100
        ),
        0
    )


    gee_ccaa = gee_ccaa[
        gee_ccaa[
            "expedientes"
        ] >= 10
    ].copy()


    if len(gee_ccaa) > 0:

        media_gee = (
            gee_ccaa[
                "cuota_gee"
            ].mean()
        )


        fig_gee_ccaa = px.scatter(
            gee_ccaa,
            x="expedientes",
            y="cuota_gee",
            size="expedientes",
            hover_name="comunidad_autonoma",
            labels={
                "expedientes":
                    "Tamaño del mercado",
                "cuota_gee":
                    "Cuota GEE (%)"
            },
            title=(
                "Cuota de GEE frente al tamaño del mercado"
            )
        )


        fig_gee_ccaa.add_hline(
            y=media_gee,
            line_dash="dash",
            annotation_text="Media"
        )


        fig_gee_ccaa.update_layout(
            height=500,
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20
            )
        )


        st.plotly_chart(
            fig_gee_ccaa,
            use_container_width=True
        )


    # ========================================================
    # DATOS
    # ========================================================

    with st.expander(
        "Consultar datos del dashboard"
    ):

        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True
        )


        csv_dashboard = (
            df_filtrado
            .to_csv(
                index=False,
                encoding="utf-8-sig"
            )
        )


        st.download_button(
            "Descargar datos filtrados (CSV)",
            data=csv_dashboard,
            file_name=(
                "dashboard_licitaciones_filtrado.csv"
            ),
            mime="text/csv"
        )


# ============================================================
# ============================================================
# MOTOR DE LICITACIONES
# ============================================================
# ============================================================

else:

    st.title(
        "Motor de Licitaciones GEE"
    )

    st.write(
        "Analiza oportunidades de licitación y obtiene "
        "un ranking automático de participación."
    )


    # ========================================================
    # CARGAR EXCEL
    # ========================================================

    st.header(
        "1. Cargar licitaciones"
    )


    archivo = st.file_uploader(
        "Sube el Excel de licitaciones",
        type=[
            "xlsx",
            "xls"
        ]
    )


    # ========================================================
    # PROCESAR
    # ========================================================

    if archivo is not None:

        try:

            with st.spinner(
                "Procesando licitaciones..."
            ):

                df_resultado = procesar_excel(
                    archivo.getvalue()
                )


            st.success(
                f"Procesamiento completado: "
                f"{len(df_resultado):,} oportunidades válidas."
            )


        except Exception as e:

            st.error(
                "No se ha podido procesar el archivo."
            )

            st.exception(e)

            st.stop()


        # ====================================================
        # RESULTADO AUTOMÁTICO
        # ====================================================

        st.header(
            "2. Resultado automático"
        )


        col1, col2, col3, col4 = st.columns(4)


        with col1:

            st.metric(
                "Oportunidades",
                f"{len(df_resultado):,}"
            )


        with col2:

            st.metric(
                "Score medio",
                f"{df_resultado['score_final'].mean():.2f}"
            )


        with col3:

            st.metric(
                "Score máximo",
                f"{df_resultado['score_final'].max():.2f}"
            )


        with col4:

            st.metric(
                "Score ≥ 80",
                int(
                    (
                        df_resultado[
                            "score_final"
                        ]
                        >= 80
                    ).sum()
                )
            )


        # ====================================================
        # RANKING
        # ====================================================

        st.header(
            "3. Ranking de oportunidades"
        )


        columnas_ranking = [
            "Número de expediente",
            "Órgano de Contratación",
            "Objeto",
            "Estado",
            "presupuesto_mensual",
            "score_ml",
            "ajuste_presupuesto",
            "bonus_grupo_gee",
            "ajuste_cpv_504",
            "score_final"
        ]


        columnas_ranking = [
            col
            for col in columnas_ranking
            if col in df_resultado.columns
        ]


        ranking = (
            df_resultado[
                columnas_ranking
            ]
            .sort_values(
                "score_final",
                ascending=False
            )
            .reset_index(
                drop=True
            )
            .copy()
        )


        ranking.insert(
            0,
            "Ranking",
            range(
                1,
                len(ranking) + 1
            )
        )


        st.dataframe(
            ranking,
            use_container_width=True,
            hide_index=True
        )


        # ====================================================
        # EVALUACIÓN MANUAL
        # ====================================================

        st.header(
            "4. Evaluación manual opcional"
        )


        realizar_manual = st.checkbox(
            "Quiero realizar una evaluación manual",
            value=False
        )


        if not realizar_manual:

            st.info(
                "La evaluación manual es opcional. "
                "El ranking automático mostrado arriba "
                "es el resultado principal."
            )


        else:

            # =================================================
            # SELECCIÓN
            # =================================================

            st.subheader(
                "Selecciona una oportunidad"
            )


            df_selector = (
                df_resultado[
                    [
                        "Número de expediente",
                        "Órgano de Contratación",
                        "Objeto",
                        "score_final",
                        "presupuesto_mensual"
                    ]
                ]
                .sort_values(
                    "score_final",
                    ascending=False
                )
                .reset_index(
                    drop=True
                )
            )


            opciones = []

            expediente_por_etiqueta = {}


            for _, fila in df_selector.iterrows():

                expediente = str(
                    fila[
                        "Número de expediente"
                    ]
                )


                cliente = str(
                    fila[
                        "Órgano de Contratación"
                    ]
                )


                score = float(
                    fila[
                        "score_final"
                    ]
                )


                etiqueta = (
                    f"{score:.2f} | "
                    f"{expediente} | "
                    f"{cliente}"
                )


                opciones.append(
                    etiqueta
                )


                expediente_por_etiqueta[
                    etiqueta
                ] = expediente


            seleccion = st.selectbox(
                "Licitación",
                opciones
            )


            expediente_seleccionado = (
                expediente_por_etiqueta[
                    seleccion
                ]
            )


            # =================================================
            # RECUPERAR FILA
            # =================================================

            fila_seleccionada = df_resultado[
                df_resultado[
                    "Número de expediente"
                ]
                .astype(str)
                .str.strip()
                .eq(
                    expediente_seleccionado.strip()
                )
            ]


            if len(
                fila_seleccionada
            ) != 1:

                st.error(
                    "No se ha podido identificar "
                    "de forma única la oportunidad."
                )

                st.stop()


            fila = (
                fila_seleccionada
                .iloc[0]
            )


            # =================================================
            # INFORMACIÓN
            # =================================================

            st.subheader(
                "Información de la oportunidad"
            )


            st.write(
                f"**Número de expediente:** "
                f"{fila['Número de expediente']}"
            )


            st.write(
                f"**Cliente:** "
                f"{fila['Órgano de Contratación']}"
            )


            st.write(
                f"**Objeto:** "
                f"{fila['Objeto']}"
            )


            st.write(
                f"**Score automático:** "
                f"{fila['score_final']:.2f}"
            )


            st.write(
                f"**Presupuesto mensual:** "
                f"{fila['presupuesto_mensual']:.2f} €/mes"
            )


            # =================================================
            # INPUTS MANUALES
            # =================================================

            st.subheader(
                "Datos manuales"
            )


            col1, col2, col3 = st.columns(3)


            with col1:

                tecnicos = st.number_input(
                    "Técnicos",
                    min_value=0,
                    value=0,
                    step=1
                )


            with col2:

                vehiculos = st.number_input(
                    "Vehículos",
                    min_value=0,
                    value=0,
                    step=1
                )


            with col3:

                responsables = st.number_input(
                    "Responsables",
                    min_value=0,
                    value=0,
                    step=1
                )


            estrategica = st.checkbox(
                "Es estratégica para Grupo GEE",
                value=False
            )


            # =================================================
            # BOTÓN
            # =================================================

            calcular = st.button(
                "Calcular score manual",
                type="primary"
            )


            # =================================================
            # RESULTADO
            # =================================================

            if calcular:

                try:

                    resultado_manual = (
                        motor.evaluar_manual(
                            df_resultado,
                            expediente=(
                                expediente_seleccionado
                            ),
                            tecnicos=int(
                                tecnicos
                            ),
                            vehiculos=int(
                                vehiculos
                            ),
                            responsables=int(
                                responsables
                            ),
                            estrategica=(
                                estrategica
                            )
                        )
                    )


                except Exception as e:

                    st.error(
                        "No se ha podido calcular "
                        "el score manual."
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


                # =============================================
                # ECONOMÍA
                # =============================================

                st.write(
                    "### Cálculo económico"
                )


                datos_economicos = pd.DataFrame(
                    {
                        "Concepto": [
                            "Presupuesto mensual",
                            "Coste técnicos",
                            "Coste vehículos",
                            "Coste responsables",
                            "Coste total recursos",
                            "Presupuesto mensual ajustado",
                            "Ajuste económico automático",
                            "Ajuste económico manual"
                        ],
                        "Importe": [
                            resultado_manual[
                                "presupuesto_mensual"
                            ],
                            resultado_manual[
                                "coste_tecnicos"
                            ],
                            resultado_manual[
                                "coste_vehiculos"
                            ],
                            resultado_manual[
                                "coste_responsables"
                            ],
                            resultado_manual[
                                "coste_total_recursos"
                            ],
                            resultado_manual[
                                "presupuesto_mensual_ajustado"
                            ],
                            resultado_manual[
                                "ajuste_economico_automatico"
                            ],
                            resultado_manual[
                                "ajuste_economico_manual"
                            ]
                        ]
                    }
                )


                st.dataframe(
                    datos_economicos,
                    use_container_width=True,
                    hide_index=True
                )


                # =============================================
                # ESTRATEGIA
                # =============================================

                st.write(
                    "### Factor estratégico"
                )


                st.write(
                    "Estratégica: "
                    +
                    (
                        "Sí"
                        if resultado_manual[
                            "estrategica"
                        ]
                        else "No"
                    )
                )


                st.write(
                    f"Bonus estratégico: "
                    f"+{resultado_manual['bonus_estrategico']}"
                )


                # =============================================
                # MENSAJE
                # =============================================

                if (
                    resultado_manual[
                        "variacion"
                    ]
                    < 0
                ):

                    st.warning(
                        f"El score manual baja "
                        f"{abs(resultado_manual['variacion']):.2f} "
                        f"puntos respecto al automático."
                    )


                elif (
                    resultado_manual[
                        "variacion"
                    ]
                    > 0
                ):

                    st.success(
                        f"El score manual aumenta "
                        f"{resultado_manual['variacion']:.2f} "
                        f"puntos respecto al automático."
                    )


                else:

                    st.info(
                        "La evaluación manual no modifica "
                        "el score automático."
                    )
