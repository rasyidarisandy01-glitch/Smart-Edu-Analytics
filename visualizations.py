"""Plotly figure factories used by the Streamlit interface."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import KKM
from data_utils import get_class_monthly_averages, get_subject_averages


def individual_monthly_trend(dataframe):
    chart_data = dataframe.groupby(
        'Bulan', observed=False
    )['Nilai'].mean().reset_index()
    chart_data = chart_data.dropna(subset=['Nilai'])
    if chart_data.empty:
        return None

    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=chart_data['Bulan'].astype(str),
        y=chart_data['Nilai'],
        mode='lines+markers',
        name='Nilai Rata-rata',
        line=dict(color='#2E8B57', width=3),
        marker=dict(size=8, color='#2E8B57')
    ))
    figure.update_layout(
        title='Pergerakan Nilai',
        xaxis_title='Bulan',
        yaxis_title='Nilai',
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return figure


def student_subject_radar(dataframe):
    if not {'Mata Pelajaran', 'Nilai'}.issubset(dataframe.columns):
        return None

    radar_data = dataframe.reindex(
        columns=['Mata Pelajaran', 'Nilai']
    ).copy()
    radar_data['Mata Pelajaran'] = (
        radar_data['Mata Pelajaran'].astype('string').str.strip()
    )
    radar_data['Nilai'] = pd.to_numeric(
        radar_data['Nilai'], errors='coerce'
    )
    radar_data = radar_data.dropna(subset=['Mata Pelajaran', 'Nilai'])
    radar_data = radar_data.loc[radar_data['Mata Pelajaran'] != '']
    subject_averages = (
        radar_data.groupby('Mata Pelajaran', as_index=False)['Nilai']
        .mean()
        .sort_values('Mata Pelajaran')
    )
    if subject_averages.empty:
        return None

    figure = px.line_polar(
        subject_averages,
        r='Nilai',
        theta='Mata Pelajaran',
        line_close=True,
        markers=True
    )
    figure.update_traces(
        fill='toself',
        fillcolor='rgba(99, 110, 250, 0.25)',
        line=dict(color='#636EFA', width=2),
        marker=dict(color='#636EFA', size=7)
    )
    figure.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#E6EAF2',
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                showline=False,
                gridcolor='rgba(230, 234, 242, 0.25)',
                tickfont=dict(color='#E6EAF2')
            ),
            angularaxis=dict(
                gridcolor='rgba(230, 234, 242, 0.25)',
                tickfont=dict(color='#E6EAF2')
            )
        )
    )
    return figure


def topic_average_bar(dataframe):
    topic_data = (
        dataframe.groupby('Topik', observed=True)['Nilai']
        .mean()
        .reset_index()
        .sort_values(by='Nilai', ascending=False)
    )
    if topic_data.empty:
        return None

    figure = px.bar(
        topic_data,
        x='Topik',
        y='Nilai',
        color='Nilai',
        color_continuous_scale='Blues',
        text_auto='.2f'
    )
    figure.update_layout(
        title='Rata-rata Nilai Berdasarkan Materi',
        xaxis_title='Topik Materi',
        yaxis_title='Rata-rata Nilai',
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return figure


def class_monthly_trend(dataframe):
    monthly_data = get_class_monthly_averages(dataframe)
    if monthly_data.empty:
        return None

    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=monthly_data['Bulan'].astype(str),
        y=monthly_data['Nilai'],
        mode='lines+markers',
        name='Rata-rata kelas',
        line=dict(color='#2E8B57', width=3),
        marker=dict(size=8)
    ))
    figure.update_layout(
        xaxis_title='Bulan',
        yaxis_title='Rata-rata Nilai',
        height=350,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    figure.update_xaxes(
        categoryorder='array',
        categoryarray=monthly_data['Bulan'].astype(str).tolist()
    )
    return figure


def class_topic_average_bar(topic_averages):
    if topic_averages.empty:
        return None

    topic_data = topic_averages.sort_values(
        ['Nilai', 'Topik'], ascending=[True, True]
    ).copy()
    topic_data['Di bawah KKM'] = topic_data['Nilai'] < KKM
    figure = px.bar(
        topic_data,
        x='Nilai',
        y='Topik',
        orientation='h',
        color='Di bawah KKM',
        color_discrete_map={True: '#8B0000', False: '#2E8B57'},
        hover_data={'Di bawah KKM': False},
        labels={'Nilai': 'Rata-rata Nilai', 'Topik': 'Topik Materi'}
    )
    figure.update_yaxes(
        categoryorder='array',
        categoryarray=topic_data['Topik'].tolist(),
        autorange='reversed'
    )
    figure.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=False
    )
    return figure


def subject_average_bar(dataframe):
    subject_data = get_subject_averages(dataframe)
    if subject_data.empty:
        return None

    figure = px.bar(
        subject_data,
        x='Mata Pelajaran',
        y='Nilai',
        color='Mata Pelajaran',
        text_auto='.1f',
        labels={
            'Mata Pelajaran': 'Mata Pelajaran',
            'Nilai': 'Rata-rata Nilai'
        }
    )
    figure.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=False
    )
    figure.update_yaxes(title='Rata-rata Nilai')
    return figure

