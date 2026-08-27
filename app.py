import io

import cloudpickle
import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Motor de Licitaciones GEE",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# MOTOR
# ============================================================

@st.cache_resource
def cargar_motor():

    with open(
        "motor_licitaciones_final.pkl",
        "rb"
    ) as f:

        return cloudpickle.load(f)


try:

    motor = cargar_motor()

except Exception as e:

    st.error(
        "No se ha podido cargar el motor de licitaciones."
    )

    st.exception(e)

    st.stop()


# ============================================================
# PROCESAR EXCEL
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
# CABECERA
# ============================================================

st.title(
    "Motor de Licitaciones GEE"
)

st.write(
    "Analiza oportunidades de licitación y obtiene "
    "un ranking automático de participación."
)


# ============================================================
# SUBIDA DEL EXCEL
# ============================================================

st.header(
    "1. Cargar licitaciones"
)

archivo = st.file_uploader(
    "Sube el Excel de licitaciones",
    type=["xlsx", "xls"]
)


# ============================================================
# PROCESAMIENTO
# ============================================================

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


    # ========================================================
    # RESUMEN AUTOMÁTICO
    # ========================================================

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
                    ] >= 80
                ).sum()
            )
        )


    # ========================================================
    # RANKING
    # ========================================================

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
        .reset_index(drop=True)
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


    # ========================================================
    # EVALUACIÓN MANUAL
    # ========================================================

    st.header(
        "4. Evaluación manual opcional"
    )

    realizar_manual = st.checkbox(
        "Quiero realizar una evaluación manual",
        value=False
    )


    # ========================================================
    # SI NO SE QUIERE MANUAL
    # ========================================================

    if not realizar_manual:

        st.info(
            "La evaluación manual es opcional. "
            "El ranking automático mostrado arriba "
            "es el resultado principal."
        )


    # ========================================================
    # EVALUACIÓN MANUAL
    # ========================================================

    else:

        st.subheader(
            "Selecciona una oportunidad"
        )

        # ----------------------------------------------------
        # ORDENAR PARA EL DESPLEGABLE
        # ----------------------------------------------------

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
            .reset_index(drop=True)
        )


        # ----------------------------------------------------
        # OPCIONES
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # SELECTOR
        # ----------------------------------------------------

        seleccion = st.selectbox(
            "Licitación",
            opciones
        )

        expediente_seleccionado = (
            expediente_por_etiqueta[
                seleccion
            ]
        )


        # ----------------------------------------------------
        # RECUPERAR OPORTUNIDAD
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # INFORMACIÓN
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # INPUTS MANUALES
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # BOTÓN
        # ----------------------------------------------------

        calcular = st.button(
            "Calcular score manual",
            type="primary"
        )


        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        if calcular:

            try:

                resultado_manual = (
                    motor.evaluar_manual(
                        df_resultado,
                        expediente=(
                            expediente_seleccionado
                        ),
                        tecnicos=int(tecnicos),
                        vehiculos=int(vehiculos),
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


            # ------------------------------------------------
            # DATOS ECONÓMICOS
            # ------------------------------------------------

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


            # ------------------------------------------------
            # ESTRATEGIA
            # ------------------------------------------------

            st.write(
                "### Factor estratégico"
            )

            st.write(
                "Estratégica: "
                + (
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


            # ------------------------------------------------
            # RESULTADO FINAL
            # ------------------------------------------------

            if (
                resultado_manual[
                    "variacion"
                ] < 0
            ):

                st.warning(
                    f"El score manual baja "
                    f"{abs(resultado_manual['variacion']):.2f} "
                    f"puntos respecto al automático."
                )

            elif (
                resultado_manual[
                    "variacion"
                ] > 0
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
