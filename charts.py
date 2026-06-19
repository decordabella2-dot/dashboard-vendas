import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date, timedelta

CORES = {
    "Shopee": "#EE4D2D",
    "Mercado Livre HL": "#FFE600",
    "Mercado Livre Dabella": "#F5A623",
    "Amazon HL": "#FF9900",
    "TikTok Dabella": "#010101",
    "TikTok HL": "#69C9D0",
}

CORES_TEXTO = {
    "Mercado Livre HL": "#333333",
}


def _fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def grafico_linha_conta(df: pd.DataFrame, conta: str) -> go.Figure:
    df_c = df[df["conta"] == conta].copy()
    df_c = df_c.sort_values("data")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_c["data"].astype(str),
        y=df_c["valor"],
        mode="lines+markers",
        name=conta,
        line=dict(color=CORES.get(conta, "#4C72B0"), width=2.5),
        marker=dict(size=6),
        hovertemplate="<b>%{x}</b><br>" + _fmt_brl(0).replace("0", "%{y:,.2f}") + "<extra></extra>",
    ))
    fig.update_layout(
        title=f"Evolução diária — {conta}",
        xaxis_title="Data",
        yaxis_title="Faturamento (R$)",
        hovermode="x unified",
        plot_bgcolor="white",
        yaxis=dict(tickprefix="R$ ", separatethousands=True),
    )
    return fig


def grafico_barras_diario(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    totais = df.groupby("data")["valor"].sum().reset_index().sort_values("data")
    fig = go.Figure(go.Bar(
        x=totais["data"].astype(str),
        y=totais["valor"],
        marker_color="#4C72B0",
        hovertemplate="<b>%{x}</b><br>Total: R$ %{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        title="Faturamento total por dia",
        xaxis_title="Data",
        yaxis_title="Total (R$)",
        plot_bgcolor="white",
        yaxis=dict(tickprefix="R$ ", separatethousands=True),
    )
    return fig


def grafico_linhas_comparativo(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for conta in df["conta"].unique():
        df_c = df[df["conta"] == conta].sort_values("data")
        fig.add_trace(go.Scatter(
            x=df_c["data"].astype(str),
            y=df_c["valor"],
            mode="lines+markers",
            name=conta,
            line=dict(color=CORES.get(conta, "#999"), width=2),
            marker=dict(size=5),
            hovertemplate=f"<b>{conta}</b><br>%{{x}}<br>R$ %{{y:,.2f}}<extra></extra>",
        ))
    fig.update_layout(
        title="Comparativo entre contas",
        xaxis_title="Data",
        yaxis_title="Faturamento (R$)",
        hovermode="x unified",
        plot_bgcolor="white",
        yaxis=dict(tickprefix="R$ ", separatethousands=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def grafico_pizza_participacao(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    totais = df.groupby("conta")["valor"].sum().reset_index()
    totais = totais[totais["valor"] > 0]
    cores = [CORES.get(c, "#999") for c in totais["conta"]]
    fig = go.Figure(go.Pie(
        labels=totais["conta"],
        values=totais["valor"],
        marker=dict(colors=cores),
        hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>",
        textinfo="label+percent",
    ))
    fig.update_layout(title="Participação por conta no período")
    return fig


def grafico_barras_empilhadas(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    pivot = df.pivot_table(index="data", columns="conta", values="valor", aggfunc="sum", fill_value=0)
    pivot = pivot.sort_index()
    fig = go.Figure()
    for conta in pivot.columns:
        fig.add_trace(go.Bar(
            x=pivot.index.astype(str),
            y=pivot[conta],
            name=conta,
            marker_color=CORES.get(conta, "#999"),
            hovertemplate=f"<b>{conta}</b><br>%{{x}}<br>R$ %{{y:,.2f}}<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack",
        title="Faturamento por conta (empilhado)",
        xaxis_title="Data",
        yaxis_title="Total (R$)",
        plot_bgcolor="white",
        yaxis=dict(tickprefix="R$ ", separatethousands=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def grafico_barras_semanas(df: pd.DataFrame, conta: str) -> go.Figure:
    df_c = df[df["conta"] == conta].copy()
    if df_c.empty:
        return go.Figure()
    df_c["semana"] = pd.to_datetime(df_c["data"].astype(str)).dt.isocalendar().week.astype(str)
    df_c["ano"] = pd.to_datetime(df_c["data"].astype(str)).dt.year.astype(str)
    df_c["label"] = "Sem " + df_c["semana"] + "/" + df_c["ano"]
    totais = df_c.groupby("label")["valor"].sum().reset_index()
    fig = go.Figure(go.Bar(
        x=totais["label"],
        y=totais["valor"],
        marker_color=CORES.get(conta, "#4C72B0"),
        hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        title=f"Faturamento semanal — {conta}",
        xaxis_title="Semana",
        yaxis_title="Total (R$)",
        plot_bgcolor="white",
        yaxis=dict(tickprefix="R$ ", separatethousands=True),
    )
    return fig
