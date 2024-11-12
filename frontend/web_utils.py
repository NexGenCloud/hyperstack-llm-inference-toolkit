from typing import Literal

import streamlit as st
from streamlit.errors import StreamlitAPIException

from hyperstack_utils import check_password


def initialize_page(
    page_layout: Literal["wide", "centered"] | None = "wide", title: str | None = None
):
    if page_layout:
        try:
            st.set_page_config(layout=page_layout, page_title=title)
        except StreamlitAPIException:
            # probably already set
            pass

    if not check_password():
        st.stop()

    init_sidebar()

    if title:
        st.title(title)


def init_sidebar():
    st.sidebar.image("media/hyperstack-wordmark.png")
    st.sidebar.divider()
    st.sidebar.subheader("Navigation")
    st.sidebar.page_link("home.py", label="🏠 Home")
    st.sidebar.page_link("pages/models.py", label="⚙️ Models")
    st.sidebar.page_link("pages/playground.py", label="👩‍💻 Playground")
    st.sidebar.page_link("pages/api_keys.py", label="🔑 API Keys")
    st.sidebar.page_link("pages/monitoring.py", label="📊 Monitoring")


def change_user_id():
    # saving in other session state to save it across pages
    st.session_state["user_id"] = st.session_state["user_id_input"]
    st.session_state["api_key"] = None


def reset_custom_model_input():
    st.session_state["custom_model_input"] = ""


def reset_model_name_input():
    st.session_state["model_name_input"] = ""


def get_model_name_selection(models, allow_custom_model=False):
    custom_model = None
    model_name = st.selectbox(
        "Select a model",
        models,
        key="model_name_input",
        on_change=reset_custom_model_input,
    )

    if allow_custom_model:
        custom_model = st.text_input(
            "_or enter a custom model_",
            key="custom_model_input",
            on_change=reset_model_name_input,
        )

    selected_model_name = None
    if custom_model:
        selected_model_name = custom_model
    elif model_name:
        selected_model_name = model_name

    # save model in seperate session state to save it across pages
    st.session_state["model_name"] = selected_model_name

    return selected_model_name


@st.dialog("Help", width="large")
def show_page_dialog(help_str):
    st.markdown(help_str)


def sidebar_page_link(help_str):
    st.sidebar.divider()
    st.sidebar.subheader("Help")
    col1, col2, col3 = st.sidebar.columns(3)

    if st.sidebar.button("❓", use_container_width=True):
        show_page_dialog(help_str)
