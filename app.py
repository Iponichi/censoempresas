import csv
import io
from datetime import date
from typing import Any

import streamlit as st

from data_access import (
    get_cities,
    get_epigraph_options,
    get_provinces,
    search_companies_detail,
    search_companies_summary,
)

st.set_page_config(page_title="Censo de Empresas", layout="wide")

st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        background-color: #B10F2E;
    }

    section[data-testid="stSidebar"] * {
        color: white;
    }

    /* Menos espacio general del sidebar */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
        padding-bottom: 0.75rem;
    }

    /* Menos espacio arriba en la zona principal */
    section.main > div.block-container {
        padding-top: 1.2rem;
    }

    /* Labels más compactos */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {
        color: white !important;
        margin-bottom: 0.15rem !important;
    }

    /* Radios */
    section[data-testid="stSidebar"] [role="radiogroup"] {
        gap: 0.15rem !important;
    }

    section[data-testid="stSidebar"] [role="radiogroup"] label {
        padding: 0.18rem 0.45rem;
        border-radius: 0.4rem;
        margin-bottom: 0.1rem;
        display: flex;
        align-items: center;
        min-height: 1.9rem;
    }

    section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background-color: #8E0C25;
        border-left: 4px solid #FFFFFF;
        font-weight: 700;
    }

    /* Inputs texto/fecha */
    section[data-testid="stSidebar"] .stTextInput input,
    section[data-testid="stSidebar"] .stDateInput input {
        background-color: #F7F1F2 !important;
        color: #2B161A !important;
        height: 1.95rem !important;
        min-height: 1.95rem !important;
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        border-radius: 0.42rem !important;
    }

    section[data-testid="stSidebar"] .stTextInput input::placeholder,
    section[data-testid="stSidebar"] .stDateInput input::placeholder {
        color: #7A5A60 !important;
        opacity: 1 !important;
    }

    /* Selectbox y multiselect */
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        min-height: 1.95rem !important;
        background-color: #F7F1F2 !important;
        border-radius: 0.42rem !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    /* Texto seleccionado y textos internos */
    section[data-testid="stSidebar"] div[data-baseweb="select"] *,
    section[data-testid="stSidebar"] div[data-baseweb="select"] span,
    section[data-testid="stSidebar"] div[data-baseweb="select"] div,
    section[data-testid="stSidebar"] div[data-baseweb="select"] input {
        color: #2B161A !important;
        opacity: 1 !important;
    }

    /* Placeholder en selects */
    section[data-testid="stSidebar"] div[data-baseweb="select"] input::placeholder {
        color: #7A5A60 !important;
        opacity: 1 !important;
    }

    /* Flecha del select */
    section[data-testid="stSidebar"] div[data-baseweb="select"] svg {
        fill: #6A2C36 !important;
    }

    /* Tags seleccionadas */
    section[data-testid="stSidebar"] div[data-baseweb="tag"] {
        background-color: #D94A63 !important;
        color: white !important;
        border-radius: 0.35rem !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="tag"] span,
    section[data-testid="stSidebar"] div[data-baseweb="tag"] svg {
        color: white !important;
        fill: white !important;
    }

    /* Botones */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #8E0C25;
        color: white;
        border: 1px solid #D8AAB4;
        border-radius: 0.45rem;
        font-weight: 600;
        min-height: 1.95rem;
        padding: 0.15rem 0.7rem;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #76081D;
        color: white;
        border: 1px solid #FFFFFF;
    }

    section[data-testid="stSidebar"] .stButton > button:focus {
        box-shadow: 0 0 0 0.12rem rgba(255, 255, 255, 0.22);
        color: white;
    }

    /* Menos separación entre widgets */
    section[data-testid="stSidebar"] .stSelectbox,
    section[data-testid="stSidebar"] .stMultiSelect,
    section[data-testid="stSidebar"] .stTextInput,
    section[data-testid="stSidebar"] .stDateInput,
    section[data-testid="stSidebar"] .stRadio,
    section[data-testid="stSidebar"] .stButton {
        margin-bottom: 0.28rem !important;
    }

    /* Encabezados un poco más juntos */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        margin-top: 0.4rem !important;
        margin-bottom: 0.45rem !important;
    }

    /* Caption más compacto */
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        margin-top: 0.15rem !important;
        margin-bottom: 0.2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

header_col_left, header_col_right = st.columns([3, 1])

with header_col_left:
    st.title("Censo de Empresas")

with header_col_right:
    st.image("assets/camara_navarra.jpg", width=220)


@st.cache_data(ttl=1800)
def cached_provinces() -> list[str]:
    return get_provinces()


@st.cache_data(ttl=1800)
def cached_cities(province: str) -> list[str]:
    return get_cities(province)


@st.cache_data(ttl=1800)
def cached_epigraph_options() -> list[dict[str, str]]:
    return get_epigraph_options()


def normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def filter_epigraph_options(
    epigraph_options: list[dict[str, str]],
    search_text: str,
) -> list[dict[str, str]]:
    normalized_search = normalize_text(search_text)

    if not normalized_search:
        return epigraph_options

    search_words = normalized_search.split()

    filtered_options: list[dict[str, str]] = []
    for option in epigraph_options:
        searchable_text = normalize_text(
            f'{option.get("codigo", "")} {option.get("nombre", "")} {option.get("label", "")}'
        )

        if all(word in searchable_text for word in search_words):
            filtered_options.append(option)

    return filtered_options


def ensure_epigraph_state() -> None:
    if "selected_epigraph_labels" not in st.session_state:
        st.session_state.selected_epigraph_labels = []

    if "epigraph_search_text" not in st.session_state:
        st.session_state.epigraph_search_text = ""



def add_epigraphs_to_selection(new_labels: list[str]) -> None:
    current_labels = st.session_state.selected_epigraph_labels.copy()

    for label in new_labels:
        if label not in current_labels:
            current_labels.append(label)

    st.session_state.selected_epigraph_labels = current_labels


def remove_epigraph_from_selection(label_to_remove: str) -> None:
    st.session_state.selected_epigraph_labels = [
        label
        for label in st.session_state.selected_epigraph_labels
        if label != label_to_remove
    ]


def clear_epigraph_search_text() -> None:
    st.session_state.epigraph_search_text = ""


def convert_rows_to_csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def render_applied_filters_summary(
    temporal_mode: str,
    reference_date: date | None,
    date_from: date | None,
    date_to: date | None,
    province: str,
    cities: list[str],
    selected_epigraph_labels: list[str],
    view_mode: str,
) -> None:
    if temporal_mode == "date":
        temporal_text = "Activas en una fecha"
        date_text = reference_date.strftime("%d/%m/%Y") if reference_date else "-"
    else:
        temporal_text = "Con actividad en un rango"
        date_from_text = date_from.strftime("%d/%m/%Y") if date_from else "-"
        date_to_text = date_to.strftime("%d/%m/%Y") if date_to else "-"
        date_text = f"{date_from_text} - {date_to_text}"

    province_text = province if province else "Todas"

    st.markdown("### Filtros aplicados")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write(f"**Modo temporal:** {temporal_text}")
        st.write(f"**Fecha / rango:** {date_text}")

    with col2:
        st.write(f"**Provincia:** {province_text}")
        st.write(f"**Modo de visualización:** {view_mode}")

    with col3:
        st.write(f"**Localidades seleccionadas:** {len(cities)}")
        st.write(f"**Epígrafes aplicados al filtro:** {len(selected_epigraph_labels)}")


def render_applied_filters_detail(
    province: str,
    cities: list[str],
    selected_epigraph_labels: list[str],
) -> None:
    province_text = province if province else "Todas"
    city_items = cities if cities else ["Todas"]
    epigraph_items = selected_epigraph_labels if selected_epigraph_labels else ["Todos"]

    with st.expander("Ver detalle de filtros", expanded=False):
        st.write(f"**Provincia:** {province_text}")

        st.write("**Localidades:**")
        for city in city_items:
            st.write(f"- {city}")

        st.write("**Epígrafes:**")
        for label in epigraph_items:
            st.write(f"- {label}")


today = date.today()
default_year = today.year - 1
year_start = date(default_year, 1, 1)
year_end = date(default_year, 12, 31)

with st.sidebar:
    st.header("Filtros")

    temporal_mode = st.radio(
        "Modo temporal",
        options=["Activas en una fecha", "Con actividad en un rango"],
    )

    if temporal_mode == "Activas en una fecha":
        reference_date = st.date_input("Fecha de referencia", value=today)
        date_from = None
        date_to = None
        temporal_mode_value = "date"
    else:
        date_from = st.date_input("Fecha inicio rango", value=year_start)
        date_to = st.date_input("Fecha fin rango", value=year_end)
        reference_date = None
        temporal_mode_value = "range"

        if date_from > date_to:
            st.error("La fecha inicio no puede ser mayor que la fecha fin.")
            st.stop()

    view_mode = st.radio(
        "Modo de visualización",
        options=["Resumen por empresa", "Detalle por epígrafe"],
    )

    try:
        provinces = [""] + cached_provinces()
    except Exception as ex:
        st.error(f"Error cargando provincias: {ex}")
        st.stop()

    province = st.selectbox("Provincia", options=provinces)

    try:
        if province:
            city_options = cached_cities(province)
        else:
            city_options = []
    except Exception as ex:
        st.error(f"Error cargando localidades: {ex}")
        st.stop()

    cities = st.multiselect("Localidades", options=city_options)

    try:
        epigraph_options = cached_epigraph_options()
    except Exception as ex:
        st.error(f"Error cargando epígrafes: {ex}")
        st.stop()

    ensure_epigraph_state()

    st.subheader("Epígrafes")

    st.text_input(
        "Buscar epígrafes por código o descripción",
        key="epigraph_search_text",
        placeholder="Ejemplo: 659, comercio, transporte mercancías",
    )

    filtered_epigraph_options = filter_epigraph_options(
        epigraph_options,
        st.session_state.epigraph_search_text,
    )

    filtered_epigraph_labels = [item["label"] for item in filtered_epigraph_options]

    available_epigraph_labels = [
        label
        for label in filtered_epigraph_labels
        if label not in st.session_state.selected_epigraph_labels
    ]

    epigraphs_to_add = st.multiselect(
        "Resultados encontrados",
        options=available_epigraph_labels,
    )

    col_add, col_clear_search = st.columns(2)

    with col_add:
        if st.button("Añadir"):
            add_epigraphs_to_selection(epigraphs_to_add)
            st.rerun()

    with col_clear_search:
        st.button("Limpiar texto", on_click=clear_epigraph_search_text)


    st.caption(f"Coincidencias: {len(filtered_epigraph_labels)}")

    selected_epigraph_labels = st.multiselect(
        "Epígrafes seleccionados",
        options=st.session_state.selected_epigraph_labels,
        default=st.session_state.selected_epigraph_labels,
        key="selected_epigraph_labels_widget",
    )

    st.session_state.selected_epigraph_labels = selected_epigraph_labels

    col_remove, col_clear_all = st.columns(2)

    with col_remove:
        epigraph_to_remove = st.selectbox(
            "Quitar uno",
            options=[""] + st.session_state.selected_epigraph_labels,
            index=0,
            key="epigraph_to_remove",
        )
        if st.button("Quitar") and epigraph_to_remove:
            remove_epigraph_from_selection(epigraph_to_remove)
            st.rerun()

    with col_clear_all:
        if st.button("Vaciar selección"):
            clear_epigraph_selection()
            st.rerun()

    epigraph_codes = [
        item["codigo"]
        for item in epigraph_options
        if item["label"] in st.session_state.selected_epigraph_labels
    ]

    search_clicked = st.button("Buscar", type="primary")



if search_clicked:
    
    try:
        if view_mode == "Resumen por empresa":
            rows = search_companies_summary(
                province=province,
                cities=cities,
                epigraph_codes=epigraph_codes,
                temporal_mode=temporal_mode_value,
                reference_date=reference_date,
                date_from=date_from,
                date_to=date_to,
            )
        else:
            rows = search_companies_detail(
                province=province,
                cities=cities,
                epigraph_codes=epigraph_codes,
                temporal_mode=temporal_mode_value,
                reference_date=reference_date,
                date_from=date_from,
                date_to=date_to,
            )
    except Exception as ex:
        st.error(f"Error en la búsqueda: {ex}")
        st.stop()

    st.subheader("Resultados")

    if not rows:
        st.info("No se han encontrado resultados con los filtros seleccionados.")
    else:
        render_applied_filters_summary(
            temporal_mode=temporal_mode_value,
            reference_date=reference_date,
            date_from=date_from,
            date_to=date_to,
            province=province,
            cities=cities,
            selected_epigraph_labels=st.session_state.selected_epigraph_labels,
            view_mode=view_mode,
        )

        render_applied_filters_detail(
            province=province,
            cities=cities,
            selected_epigraph_labels=st.session_state.selected_epigraph_labels,
        )

        st.divider()

        top_left, top_right = st.columns([3, 1])

        with top_left:
            st.caption("Puedes ordenar los resultados pulsando en la cabecera de cada columna.")

        with top_right:
            st.markdown(
                f"<div style='text-align: right; margin-top: 0.2rem; "
                f"font-size: 0.95rem; color: #8a7b7f;'>"
                f"Total de registros: <strong>{len(rows)}</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.dataframe(rows, use_container_width=True, height=650)

        csv_data = convert_rows_to_csv(rows)

        st.download_button(
            label="Descargar CSV",
            data=csv_data,
            file_name="censo_empresas.csv",
            mime="text/csv",
        )