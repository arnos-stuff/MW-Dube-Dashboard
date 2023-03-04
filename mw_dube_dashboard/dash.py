import sys
import json
import subprocess
import streamlit as st
import pandas as pd
import numpy as np

import plotly.express as px
import plotly.graph_objects as pgo
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, JsCode

from mw_dube_dashboard.utils import csvPreprocessed, pkg

from functools import reduce    
from operator import and_

st.set_page_config(
    page_title="Minimum Wage Dashboard",
    page_icon="💶",
    layout="wide",
)

@st.cache_data
def get_data(year=None, country=None, nrows=None):
    return pd.read_csv(csvPreprocessed)
    # return (
    #     df[(df["Country"] == country) & (df["Year"] == year)]
    #     if year and country
    #     else df[(df["Country"] == country)]
    #     if country
    #     else df[(df["Year"] == year)]
    #     if year
    #     else df.head(nrows) if nrows else df
    # )

st.title("DataSets: Minimum Wage & Wages across the World")

mwTab, dataTab, notationTab, explanationTab, vizTab, srcTab = st.tabs([
    "Up the Minimum Wage ?",
    "Data", "Notation",
    "Explanation",
    "Visualizations",
    "Sources & References"
    ])

df = get_data()

gb = GridOptionsBuilder.from_dataframe(df)

gb.configure_pagination(enabled=True, paginationPageSize=20, paginationAutoPageSize=False)
gb.configure_selection(selection_mode="multiple", use_checkbox=False)
gb.configure_side_bar(defaultToolPanel="filters")
gb.configure_grid_options(domLayout="autoHeight")

for col in df.columns:
    if col in ["Country", "Year"]:
        gb.configure_column(col, editable=False, filter=True, enableRowGroup=True, enablePivot=True, enableValue=True)
    else:
        gb.configure_column(col, editable=False, filter=False, enableRowGroup=False, enablePivot=False, enableValue=False, aggFunc="sum")

global dfshared

dfshared = df

go = gb.build()

with dataTab:
    st.header("Data")
    
    ag = AgGrid(df,
            gridOptions=go,
            fit_columns_on_grid_load=True,
            )
    
    dfshared = ag["data"]
        

def makeLines(df, x, y, categories, markers=True, title=""):
    catvals = df[categories].unique().tolist() + ["All"]

    fig = px.line(df, x=x, y=y, color=categories, markers=True, title=title, )

    shown = df[[y, categories]].groupby(categories).mean().sort_values(by=y, ascending=False).index.tolist()
    shown = shown[:6]

    for tr in fig.data:
        tr.visible = tr.name in shown

    fig.update_layout(
        updatemenus=[
            {
                "buttons": [
                    {
                        "label": c,
                        "method": "update",
                        "args": [
                            {
                                "visible": [c in tr["name"] for tr in fig.data]
                                if c != "All"
                                else [True] * len(fig.data)
                            }
                        ],
                    }
                    for c in catvals
                ]
            }
        ]
    )

    return fig
 
with vizTab:

    plotCondition = lambda col: (
        ('wage' in col.lower() or 'income' in col.lower())
        and 'local' not in col.lower()
        and 'decile' not in col.lower()
    )

    cols = [col for col in df.columns if plotCondition(col)]

    colA, colB = st.columns(2)
    df.sort_values(by="Year", inplace=True)

    for idx, col in enumerate(cols):
        fig = makeLines(df, "Year", col, categories="Country", markers=True, title=col)
        if idx % 2 == 0:
            colA.plotly_chart(fig)
        else:
            colB.plotly_chart(fig)

with mwTab:
    st.header("Should your country up the Minimum Wage ?")

    st.markdown((pkg / "README.md").read_text())

    fig = pgo.Figure()

    buttonCol, textCol = st.columns(2)

    txtcountry = textCol.text_input(label="Country", value="United Kingdom", key="Country")

    mwcountry = buttonCol.selectbox("Select a country", df["Country"].unique())

    txtoptions = df[df["Country"].str.lower().str.contains(txtcountry)]["Country"].unique()

    txtval = txtoptions.pop() if len(txtoptions) else None


    filtcountry = mwcountry or txtval or "United Kingdom"

    dfmw = df[df["Country"] == filtcountry]

    mwcolumns = [
        "Min Wage (U.S. dollars)",
        "Avg Wage (U.S. dollars)",
        "Average of income (deciles)"
        ]

    for mwcol in mwcolumns:
        if "decile" not in mwcol.lower():
            fig.add_trace(
                pgo.Scatter(
                    x=dfmw["Year"], y=dfmw[mwcol],
                    mode='lines+markers',
                    name=mwcol,
                    line=dict(
                        shape='spline',
                        smoothing=0.5,
                    )
                )
            )
        else:
            for decile in df["Decile"].unique():
                fig.add_trace(
                    pgo.Scatter(
                        x=dfmw["Year"], y=dfmw[dfmw["Decile"] == decile][mwcol],
                        mode='lines+markers',
                        name=f"{mwcol} - D{decile}",
                        line=dict(
                            shape='spline',
                            smoothing=0.5,
                        )
                    )
                )

    fig.update_layout(
        title=f"Minimum Wage & Wages in {mwcountry}",
        xaxis_title="Year",
        yaxis_title="Wages (U.S. Dollars)",
        legend_title="Legend",
        )

    st.markdown("## Minimum Wage & Wages in the Country")

    st.plotly_chart(fig, use_container_width=True)





with notationTab:
    st.header("Notation")
    st.markdown((pkg / "DubeNotation.md").read_text())

with explanationTab:
    st.header("Explanation")
    st.markdown((pkg / "Elasticity.md").read_text())

with srcTab:
    st.header("Sources & References")
    st.markdown((pkg / "Sources.md").read_text())