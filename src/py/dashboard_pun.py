import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import numpy as np

# Import the data loading function
import sys
import os
sys.path.append(os.path.dirname(__file__))

st.set_page_config(
    page_title="Dashboard PUN - GME",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚡ Dashboard PUN - Mercato Elettrico GME")
st.markdown("---")

@st.cache_data
def load_pun_data(year):
    """Load PUN data for the specified year"""
    # Import here to avoid circular imports
    from download_and_read_excel import (
        get_dst_dates, create_datetime_with_dst, 
        get_italian_holidays, get_fascia
    )
    import requests
    import zipfile
    import io
    
    url = f"https://www.mercatoelettrico.org/it-it/Home/Esiti/Elettricita/MGP/Statistiche/DatiStorici/moduleId/10874/controller/GmeDatiStoriciItem/action/DownloadFile?fileName=Anno{year}.zip"
    
    response = requests.get(url)
    response.raise_for_status()
    
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        excel_files = [f for f in z.namelist() if f.endswith('.xls') or f.endswith('.xlsx')]
        if not excel_files:
            raise Exception("Nessun file Excel trovato nello zip.")
        excel_filename = excel_files[0]
        with z.open(excel_filename) as excel_file:
            df = pd.read_excel(excel_file, sheet_name='Prezzi-Prices', usecols=[0, 1, 2])
    
    df.columns = ['Date', 'Hour', 'PUN Index GME']
    df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d').dt.date
    
    march_dst, october_dst = get_dst_dates(year)
    df['DateTime'] = df.apply(lambda row: create_datetime_with_dst(row, march_dst, october_dst), axis=1)
    
    italian_holidays = get_italian_holidays(year)
    df['Fascia'] = df.apply(lambda row: get_fascia(row, italian_holidays), axis=1)
    
    # Add additional columns for analysis
    df['Month'] = df['DateTime'].dt.month
    df['MonthName'] = df['DateTime'].dt.month_name()
    df['Weekday'] = df['DateTime'].dt.day_name()
    df['WeekdayNum'] = df['DateTime'].dt.weekday
    
    return df[['DateTime', 'Date', 'Hour', 'Month', 'MonthName', 'Weekday', 'WeekdayNum', 'PUN Index GME', 'Fascia']]

# Sidebar filters
st.sidebar.header("🔧 Filtri")

# Year selection
available_years = [2024, 2023, 2022]  # Can be expanded
selected_year = st.sidebar.selectbox("Anno", available_years, index=0)

# Load data
try:
    with st.spinner(f'Caricamento dati {selected_year}...'):
        df = load_pun_data(selected_year)
    st.sidebar.success(f"✅ Dati {selected_year} caricati")
except Exception as e:
    st.error(f"Errore nel caricamento dati: {e}")
    st.stop()

# Month filter
months_map = {
    1: 'Gennaio', 2: 'Febbraio', 3: 'Marzo', 4: 'Aprile',
    5: 'Maggio', 6: 'Giugno', 7: 'Luglio', 8: 'Agosto', 
    9: 'Settembre', 10: 'Ottobre', 11: 'Novembre', 12: 'Dicembre'
}
available_months = sorted(df['Month'].unique())
selected_months = st.sidebar.multiselect(
    "Mesi", 
    available_months,
    default=available_months,
    format_func=lambda x: months_map[x]
)

# Weekday filter
weekdays_map = {
    0: 'Lunedì', 1: 'Martedì', 2: 'Mercoledì', 3: 'Giovedì',
    4: 'Venerdì', 5: 'Sabato', 6: 'Domenica'
}
available_weekdays = sorted(df['WeekdayNum'].unique())
selected_weekdays = st.sidebar.multiselect(
    "Giorni della settimana",
    available_weekdays,
    default=available_weekdays,
    format_func=lambda x: weekdays_map[x]
)

# Fascia filter
available_fasce = sorted(df['Fascia'].unique())
selected_fasce = st.sidebar.multiselect(
    "Fasce orarie",
    available_fasce,
    default=available_fasce
)

# Date range filter
min_date = df['Date'].min()
max_date = df['Date'].max()
date_range = st.sidebar.date_input(
    "Range date",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Apply filters
filtered_df = df[
    (df['Month'].isin(selected_months)) &
    (df['WeekdayNum'].isin(selected_weekdays)) &
    (df['Fascia'].isin(selected_fasce))
]

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['Date'] >= start_date) & 
        (filtered_df['Date'] <= end_date)
    ]

st.sidebar.markdown("---")
st.sidebar.markdown(f"📊 **Righe filtrate**: {len(filtered_df):,}")
st.sidebar.markdown(f"📅 **Periodo**: {len(selected_months)} mesi")

if filtered_df.empty:
    st.warning("Nessun dato disponibile con i filtri selezionati")
    st.stop()

# KPI Cards
st.header("📊 Indicatori Principali")

col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_pun = filtered_df['PUN Index GME'].mean()
    st.metric("PUN Medio", f"{avg_pun:.2f} €/MWh")

with col2:
    min_pun = filtered_df['PUN Index GME'].min()
    st.metric("PUN Minimo", f"{min_pun:.2f} €/MWh")

with col3:
    max_pun = filtered_df['PUN Index GME'].max()
    st.metric("PUN Massimo", f"{max_pun:.2f} €/MWh")

with col4:
    total_hours = len(filtered_df)
    st.metric("Ore Totali", f"{total_hours:,}")

# KPI by Fascia
st.subheader("💡 PUN per Fascia Oraria")
fascia_stats = filtered_df.groupby('Fascia')['PUN Index GME'].agg(['mean', 'count']).round(2)

col1, col2, col3 = st.columns(3)
fascia_colors = {'F1': '#ff6b6b', 'F2': '#ffd93d', 'F3': '#6bcf7f'}

for i, (fascia, col) in enumerate(zip(['F1', 'F2', 'F3'], [col1, col2, col3])):
    if fascia in fascia_stats.index:
        with col:
            mean_val = fascia_stats.loc[fascia, 'mean']
            count_val = fascia_stats.loc[fascia, 'count']
            
            st.markdown(f"""
            <div style="background-color: {fascia_colors[fascia]}20; padding: 15px; border-radius: 10px; border-left: 4px solid {fascia_colors[fascia]}">
                <h3 style="margin: 0; color: {fascia_colors[fascia]}">{fascia}</h3>
                <p style="font-size: 24px; margin: 5px 0; font-weight: bold">{mean_val:.2f} €/MWh</p>
                <p style="margin: 0; font-size: 14px; opacity: 0.7">{count_val:,} ore</p>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# Time Series Plot
st.header("📈 Andamento Temporale PUN")

fig_ts = px.line(
    filtered_df, 
    x='DateTime', 
    y='PUN Index GME',
    color='Fascia',
    color_discrete_map=fascia_colors,
    title="Andamento PUN nel Tempo per Fascia"
)

fig_ts.update_layout(
    xaxis_title="Data e Ora",
    yaxis_title="PUN (€/MWh)",
    hovermode='x unified',
    height=500
)

st.plotly_chart(fig_ts, use_container_width=True)

# Two columns for additional charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("📦 Distribuzione Prezzi per Fascia")
    
    fig_box = px.box(
        filtered_df,
        x='Fascia',
        y='PUN Index GME',
        color='Fascia',
        color_discrete_map=fascia_colors,
        title="Distribuzione PUN per Fascia Oraria"
    )
    
    fig_box.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_box, use_container_width=True)

with col2:
    st.subheader("📊 PUN Medio Mensile")
    
    monthly_data = filtered_df.groupby(['MonthName', 'Fascia'])['PUN Index GME'].mean().reset_index()
    
    fig_monthly = px.bar(
        monthly_data,
        x='MonthName',
        y='PUN Index GME',
        color='Fascia',
        color_discrete_map=fascia_colors,
        title="PUN Medio Mensile per Fascia"
    )
    
    fig_monthly.update_layout(
        xaxis_title="Mese",
        yaxis_title="PUN Medio (€/MWh)",
        height=400
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

# Heatmap
st.subheader("🔥 Heatmap PUN - Giorno vs Ora")

heatmap_data = filtered_df.groupby(['Weekday', 'Hour'])['PUN Index GME'].mean().reset_index()
heatmap_pivot = heatmap_data.pivot(index='Weekday', columns='Hour', values='PUN Index GME')

# Reorder weekdays
weekday_order = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
heatmap_pivot = heatmap_pivot.reindex(weekday_order)

fig_heatmap = go.Figure(data=go.Heatmap(
    z=heatmap_pivot.values,
    x=heatmap_pivot.columns,
    y=heatmap_pivot.index,
    colorscale='RdYlBu_r',
    hoverongaps=False,
    colorbar=dict(title="PUN (€/MWh)")
))

fig_heatmap.update_layout(
    title="Heatmap PUN - Media per Giorno della Settimana e Ora",
    xaxis_title="Ora del Giorno",
    yaxis_title="Giorno della Settimana",
    height=400
)

st.plotly_chart(fig_heatmap, use_container_width=True)

# Data Table
st.subheader("📋 Dati Dettagliati")

# Show sample of filtered data
display_df = filtered_df[['DateTime', 'Hour', 'PUN Index GME', 'Fascia', 'Weekday']].copy()
display_df['DateTime'] = display_df['DateTime'].dt.strftime('%Y-%m-%d %H:%M')

st.dataframe(
    display_df.head(1000),  # Limit to first 1000 rows for performance
    use_container_width=True,
    height=300
)

if len(filtered_df) > 1000:
    st.info(f"Mostrando le prime 1000 righe di {len(filtered_df):,} totali")

# Export data option
if st.button("📥 Scarica Dati Filtrati (CSV)"):
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Clicca per scaricare",
        data=csv,
        file_name=f"pun_data_{selected_year}_filtered.csv",
        mime="text/csv"
    )