import streamlit as st
import pandas as pd
from datetime import date, timedelta
import io

import database as db
import analytics as an
import charts as ch

db.init_db()

st.set_page_config(
    page_title="Controle de Faturamento",
    page_icon="📊",
    layout="wide",
)

# ── CSS customizado ──────────────────────────────────────────────────────────
st.markdown("""
<style>
.card {
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 8px;
}
.card-neutro  { background: #f0f2f6; border-left: 5px solid #aaa; }
.card-alta    { background: #e8f5e9; border-left: 5px solid #2e7d32; }
.card-queda   { background: #ffebee; border-left: 5px solid #c62828; }
.card-title   { font-size: 13px; color: #555; margin-bottom: 4px; }
.card-valor   { font-size: 22px; font-weight: 700; }
.card-sub     { font-size: 12px; color: #777; margin-top: 4px; }
.var-alta     { color: #2e7d32; font-weight: 600; }
.var-queda    { color: #c62828; font-weight: 600; }
.var-neutro   { color: #777; }
</style>
""", unsafe_allow_html=True)


def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def card_html(titulo: str, valor: float, variacao_label: str, sub: str, status: str) -> str:
    cls_var = {"alta": "var-alta", "queda": "var-queda"}.get(status, "var-neutro")
    return f"""
    <div class="card card-{status}">
        <div class="card-title">{titulo}</div>
        <div class="card-valor">{brl(valor)}</div>
        <div class="card-sub"><span class="{cls_var}">{variacao_label}</span> &nbsp;{sub}</div>
    </div>"""


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 Faturamento")
    st.divider()

    hoje = st.date_input("Data de referência", value=date.today())
    st.divider()

    threshold_queda = st.slider("Alerta de queda (%)", -50, -1, -10)
    threshold_alta  = st.slider("Alerta de crescimento (%)", 1, 100, 10)
    st.divider()

    periodo_inicio = st.date_input("Período — início", value=hoje - timedelta(days=30))
    periodo_fim    = st.date_input("Período — fim",    value=hoje)
    st.divider()

    df_exp = db.buscar_por_periodo(periodo_inicio, periodo_fim)
    if not df_exp.empty:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df_exp.to_excel(writer, index=False, sheet_name="Faturamento")
        st.download_button(
            "⬇ Exportar Excel",
            data=buf.getvalue(),
            file_name=f"faturamento_{periodo_inicio}_{periodo_fim}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Lançar dados",
    "📋 Dashboard geral",
    "🏪 Por conta",
    "📈 Comparativo",
])

df_periodo = db.buscar_por_periodo(periodo_inicio, periodo_fim)
df_todos   = db.buscar_todos()

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — Lançar dados
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("Lançar faturamento")

    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 3, 2, 1])
    with col_f1:
        data_lanc = st.date_input("Data", value=hoje, key="data_lanc")
    with col_f2:
        conta_lanc = st.selectbox("Conta", db.CONTAS, key="conta_lanc")
    with col_f3:
        valor_lanc = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f", key="valor_lanc")
    with col_f4:
        st.write("")
        st.write("")
        if st.button("Salvar", use_container_width=True):
            db.inserir_ou_atualizar(str(data_lanc), conta_lanc, valor_lanc)
            st.success(f"Salvo: {conta_lanc} em {data_lanc} = {brl(valor_lanc)}")
            st.rerun()

    st.divider()
    st.subheader("Últimos registros")

    df_rec = db.buscar_por_periodo(hoje - timedelta(days=14), hoje)
    if df_rec.empty:
        st.info("Nenhum dado registrado ainda. Use o formulário acima para começar.")
    else:
        df_pivot = df_rec.pivot_table(
            index="data", columns="conta", values="valor", aggfunc="sum"
        ).fillna(0).sort_index(ascending=False)
        df_pivot.index = df_pivot.index.astype(str)
        df_pivot.columns.name = None

        # Formata como BRL para exibição
        st.dataframe(
            df_pivot.style.format(lambda v: brl(v) if v > 0 else "—"),
            use_container_width=True,
        )

    st.divider()
    st.subheader("Excluir registro")
    col_d1, col_d2, col_d3 = st.columns([2, 3, 1])
    with col_d1:
        data_del = st.date_input("Data", value=hoje, key="data_del")
    with col_d2:
        conta_del = st.selectbox("Conta", db.CONTAS, key="conta_del")
    with col_d3:
        st.write("")
        st.write("")
        if st.button("Excluir", use_container_width=True):
            db.deletar_registro(str(data_del), conta_del)
            st.warning(f"Registro excluído: {conta_del} em {data_del}")
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — Dashboard geral
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.header(f"Dashboard — {hoje.strftime('%d/%m/%Y')}")

    resumo = an.resumo_por_conta(df_todos, hoje, threshold_queda, threshold_alta)

    # Cards de totais consolidados
    comp_dia = an.comparativo_dia(df_todos, None, hoje)
    comp_sem = an.comparativo_semana(df_todos, None, hoje)
    comp_mes = an.comparativo_mes(df_todos, None, hoje)

    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.markdown(card_html(
            "Total hoje", comp_dia["atual"], comp_dia["label"],
            f"vs {brl(comp_dia['anterior'])} ontem",
            an.alerta_status(comp_dia["pct"], threshold_queda, threshold_alta),
        ), unsafe_allow_html=True)
    with col_t2:
        st.markdown(card_html(
            f"Semana ({comp_sem['periodo_atual']})", comp_sem["atual"], comp_sem["label"],
            f"vs {brl(comp_sem['anterior'])} ({comp_sem['periodo_anterior']})",
            an.alerta_status(comp_sem["pct"], threshold_queda, threshold_alta),
        ), unsafe_allow_html=True)
    with col_t3:
        st.markdown(card_html(
            f"Mês ({comp_mes['periodo_atual']})", comp_mes["atual"], comp_mes["label"],
            f"vs {brl(comp_mes['anterior'])} ({comp_mes['periodo_anterior']})",
            an.alerta_status(comp_mes["pct"], threshold_queda, threshold_alta),
        ), unsafe_allow_html=True)

    st.divider()
    st.subheader("Situação por conta — hoje vs ontem")

    alertas_queda = [r for r in resumo if r["status"] == "queda"]
    if alertas_queda:
        st.error(f"⚠️ {len(alertas_queda)} conta(s) com queda acentuada: " +
                 ", ".join(r["conta"] for r in alertas_queda))

    cols = st.columns(3)
    for i, r in enumerate(resumo):
        with cols[i % 3]:
            st.markdown(card_html(
                r["conta"], r["hoje"], r["var_dia_label"],
                f"vs {brl(r['ontem'])} ontem",
                r["status"],
            ), unsafe_allow_html=True)

    st.divider()
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.plotly_chart(ch.grafico_barras_diario(df_periodo), use_container_width=True)
    with col_g2:
        st.plotly_chart(ch.grafico_barras_empilhadas(df_periodo), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — Por conta
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    conta_sel = st.selectbox("Selecione a conta", db.CONTAS, key="conta_tab3")

    comp_d = an.comparativo_dia(df_todos, conta_sel, hoje)
    comp_s = an.comparativo_semana(df_todos, conta_sel, hoje)
    comp_m = an.comparativo_mes(df_todos, conta_sel, hoje)
    proj   = an.projecao_mes(df_todos, conta_sel, hoje)

    st.subheader(f"Análise — {conta_sel}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(card_html(
            "Hoje", comp_d["atual"], comp_d["label"],
            f"vs ontem {brl(comp_d['anterior'])}",
            an.alerta_status(comp_d["pct"], threshold_queda, threshold_alta),
        ), unsafe_allow_html=True)
    with col2:
        st.markdown(card_html(
            f"Semana ({comp_s['periodo_atual']})", comp_s["atual"], comp_s["label"],
            f"sem. ant. {brl(comp_s['anterior'])}",
            an.alerta_status(comp_s["pct"], threshold_queda, threshold_alta),
        ), unsafe_allow_html=True)
    with col3:
        st.markdown(card_html(
            f"Mês ({comp_m['periodo_atual']})", comp_m["atual"], comp_m["label"],
            f"mês ant. {brl(comp_m['anterior'])}",
            an.alerta_status(comp_m["pct"], threshold_queda, threshold_alta),
        ), unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="card card-neutro">
            <div class="card-title">Projeção do mês</div>
            <div class="card-valor">{brl(proj['projecao'])}</div>
            <div class="card-sub">Faturado: {brl(proj['faturado'])} | Média/dia: {brl(proj['media_diaria'])}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    df_conta = df_periodo[df_periodo["conta"] == conta_sel]
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.plotly_chart(ch.grafico_linha_conta(df_conta, conta_sel), use_container_width=True)
    with col_g2:
        st.plotly_chart(ch.grafico_barras_semanas(df_conta, conta_sel), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — Comparativo entre contas
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    st.header("Comparativo entre contas")

    if df_periodo.empty:
        st.info("Sem dados no período selecionado.")
    else:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.plotly_chart(ch.grafico_linhas_comparativo(df_periodo), use_container_width=True)
        with col_g2:
            st.plotly_chart(ch.grafico_pizza_participacao(df_periodo), use_container_width=True)

        st.divider()
        st.subheader("Ranking do período")
        ranking = (
            df_periodo.groupby("conta")["valor"]
            .sum()
            .reset_index()
            .sort_values("valor", ascending=False)
            .rename(columns={"conta": "Conta", "valor": "Total"})
        )
        ranking["Total"] = ranking["Total"].apply(brl)
        ranking.index = range(1, len(ranking) + 1)
        st.dataframe(ranking, use_container_width=True)
