import pandas as pd
import calendar
from datetime import date, timedelta


def variacao_pct(atual: float, anterior: float) -> tuple[float | None, str]:
    if anterior == 0:
        return None, "—"
    pct = ((atual - anterior) / anterior) * 100
    seta = "▲" if pct > 0 else ("▼" if pct < 0 else "→")
    return pct, f"{seta} {abs(pct):.1f}%"


def _soma(df: pd.DataFrame, conta: str | None, datas) -> float:
    mask = df["data"].isin(datas)
    if conta:
        mask &= df["conta"] == conta
    return float(df.loc[mask, "valor"].sum())


def comparativo_dia(df: pd.DataFrame, conta: str | None, hoje: date) -> dict:
    ontem = hoje - timedelta(days=1)
    atual = _soma(df, conta, [hoje])
    anterior = _soma(df, conta, [ontem])
    pct, label = variacao_pct(atual, anterior)
    return {"atual": atual, "anterior": anterior, "pct": pct, "label": label,
            "periodo_atual": str(hoje), "periodo_anterior": str(ontem)}


def comparativo_semana(df: pd.DataFrame, conta: str | None, hoje: date) -> dict:
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    inicio_ant = inicio_semana - timedelta(days=7)
    fim_ant = inicio_ant + timedelta(days=6)

    dias_atual = [inicio_semana + timedelta(days=i) for i in range(7) if (inicio_semana + timedelta(days=i)) <= hoje]
    dias_ant = [inicio_ant + timedelta(days=i) for i in range(7)]

    atual = _soma(df, conta, dias_atual)
    anterior = _soma(df, conta, dias_ant)
    pct, label = variacao_pct(atual, anterior)
    return {"atual": atual, "anterior": anterior, "pct": pct, "label": label,
            "periodo_atual": f"{inicio_semana.strftime('%d/%m')} – {min(fim_semana, hoje).strftime('%d/%m')}",
            "periodo_anterior": f"{inicio_ant.strftime('%d/%m')} – {fim_ant.strftime('%d/%m')}"}


def comparativo_mes(df: pd.DataFrame, conta: str | None, hoje: date) -> dict:
    primeiro_mes = hoje.replace(day=1)
    ultimo_dia_ant = primeiro_mes - timedelta(days=1)
    primeiro_mes_ant = ultimo_dia_ant.replace(day=1)

    dias_mes = [primeiro_mes + timedelta(days=i)
                for i in range((hoje - primeiro_mes).days + 1)]
    dias_mes_ant = [primeiro_mes_ant + timedelta(days=i)
                    for i in range(calendar.monthrange(primeiro_mes_ant.year, primeiro_mes_ant.month)[1])]

    atual = _soma(df, conta, dias_mes)
    anterior = _soma(df, conta, dias_mes_ant)
    pct, label = variacao_pct(atual, anterior)
    return {"atual": atual, "anterior": anterior, "pct": pct, "label": label,
            "periodo_atual": hoje.strftime("%b/%Y"),
            "periodo_anterior": primeiro_mes_ant.strftime("%b/%Y")}


def projecao_mes(df: pd.DataFrame, conta: str | None, hoje: date) -> dict:
    primeiro_mes = hoje.replace(day=1)
    dias_mes_total = calendar.monthrange(hoje.year, hoje.month)[1]

    dias_registrados = [primeiro_mes + timedelta(days=i)
                        for i in range((hoje - primeiro_mes).days + 1)]

    mask = df["data"].isin(dias_registrados)
    if conta:
        mask &= df["conta"] == conta

    faturado = float(df.loc[mask, "valor"].sum())
    dias_com_registro = int(df.loc[mask].groupby("data")["valor"].sum().gt(0).sum()) or 1
    media_diaria = faturado / dias_com_registro
    projecao = media_diaria * dias_mes_total
    faltam = projecao - faturado

    return {
        "faturado": faturado,
        "projecao": projecao,
        "faltam": faltam,
        "media_diaria": media_diaria,
        "dias_com_registro": dias_com_registro,
        "dias_mes_total": dias_mes_total,
    }


def alerta_status(pct: float | None, threshold_queda: float = -10, threshold_alta: float = 10) -> str:
    if pct is None:
        return "neutro"
    if pct <= threshold_queda:
        return "queda"
    if pct >= threshold_alta:
        return "alta"
    return "neutro"


def resumo_por_conta(df: pd.DataFrame, hoje: date, threshold_queda: float, threshold_alta: float) -> list[dict]:
    from database import CONTAS
    resultado = []
    for conta in CONTAS:
        comp = comparativo_dia(df, conta, hoje)
        proj = projecao_mes(df, conta, hoje)
        status = alerta_status(comp["pct"], threshold_queda, threshold_alta)
        resultado.append({
            "conta": conta,
            "hoje": comp["atual"],
            "ontem": comp["anterior"],
            "var_dia_pct": comp["pct"],
            "var_dia_label": comp["label"],
            "status": status,
            "projecao_mes": proj["projecao"],
            "faturado_mes": proj["faturado"],
        })
    return resultado
