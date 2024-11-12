import os
import pandas as pd
import requests
import streamlit as st
import plotly.express as px

from env import API_BASE_URL
from web_utils import initialize_page, sidebar_page_link

PAGE_HELP = """
## 🧭 Introduction
This page allows you to view and interact with the data stored in your databases.

## 📋 User Instructions
1. **Select a Table**: Choose a table from the dropdown list to view its data.
2. **View Data**: The data from the selected table will be displayed in a table format.
3. **Download CSV**: You can download the data as a CSV file by clicking the download button.

## 👍 Additional Tips
* You can refresh the data by re-selecting the table from the dropdown list.
* Metrics data may not be stored correctly for locally or externally deployed models.
"""


def fetch_data(endpoint):
    """
    Fetches data from a given API endpoint.

    Args:
        endpoint (str): The API endpoint to fetch data from.

    Returns:
        dict: The data fetched from the API if the request is successful, None otherwise.
    """
    response = requests.get(
        f"{API_BASE_URL}/{endpoint}",
        headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
    )
    if response.status_code != 200:
        st.error(f"Error fetching data from {endpoint}: {response.text}")
        return None
    return response.json()


def show_metrics_plot(df):
    """
    Show a plot of the metrics data.
    """
    cols = df.columns
    numerical_cols = df.select_dtypes(include=["int64", "float64"]).columns
    y_col = st.selectbox("Select Metric", numerical_cols)

    # Group by the selected interval and fill missing intervals with zero
    df.set_index("created_date_time", inplace=True)
    df = df.resample("T").sum().fillna(0).reset_index()

    fig = px.line(
        df,
        x="created_date_time",
        y=y_col,
        title=f"{y_col} over time",
        line_shape="spline",
    )
    fig.update_yaxes(rangemode="tozero")

    st.plotly_chart(fig, use_container_width=True)


def main():
    """
    The main function to initialize and run the Streamlit app.
    """
    initialize_page(title="Monitoring - Hyperstack LLM Inference Toolkit")

    sidebar_page_link(PAGE_HELP)

    table_names_response = fetch_data("tables")
    if table_names_response:
        table_names = table_names_response.get("tables", [])
        selected_table = st.selectbox("Select Table", table_names)

        if selected_table:
            table_data_response = fetch_data(f"tables/{selected_table}")
            if table_data_response:
                rows = table_data_response.get("data", [])
                if rows:
                    df = pd.DataFrame(rows)

                    if selected_table == "metric":
                        st.markdown("### Chart")
                        # created is an integer representing the timestamp
                        df["created_date_time"] = pd.to_datetime(
                            df["created"], unit="s"
                        )

                        show_metrics_plot(
                            df,
                        )

                    st.markdown("### Table")
                    col1, col2 = st.columns([5, 1])
                    csv = df.to_csv(index=False).encode("utf-8")
                    col2.download_button(
                        "💾 Download CSV",
                        csv,
                        "file.csv",
                        "text/csv",
                        key="download-csv",
                        type="primary",
                        use_container_width=True,
                    )

                    st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
