"""
PRUMO ENGENHARIA - Painel de Obras
Streamlit + Plotly, base SQLite local (prumo.db).

Rodar:
    streamlit run app.py
"""

import os
import sqlite3
import subprocess

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DB = "prumo.db"

# No Streamlit Community Cloud o disco e efemero: se o banco nao veio no repo
# (ou sumiu apos um reboot), ele e reconstruido a partir do gerador.
if not os.path.exists(DB):
    subprocess.run(["python", "gerar_dados_prumo.py"], check=True)

# ---------------------------------------------------------------- tokens
BREU     = "#0E1318"   # fundo
GRAFITE  = "#161D25"   # superficie de card
CHUMBO   = "#263140"   # linhas e bordas
CONCRETO = "#93A1B0"   # texto secundario
GIZ      = "#EEF3F8"   # texto forte
LATAO    = "#D9A441"   # acento (o peso do prumo e de latao)
APRUMADO = "#45A07E"   # dentro do plano
FORA     = "#D65A4E"   # fora do plano
ACO      = "#5E7E9E"   # linha de referencia (previsto)

st.set_page_config(page_title="Prumo Engenharia | Painel de Obras",
                   page_icon="⚖", layout="wide")

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500&display=swap" rel="stylesheet">
<style>
  .stApp {{ background:{BREU}; }}
  html, body, [class*="css"] {{ font-family:'IBM Plex Sans',sans-serif; color:{GIZ}; }}
  h1,h2,h3 {{ font-family:'Archivo',sans-serif; letter-spacing:-.02em; color:{GIZ}; }}
  section[data-testid="stSidebar"] {{ background:{GRAFITE}; border-right:1px solid {CHUMBO}; }}
  /* marca: o fio de prumo desce do topo e termina no peso */
  .marca {{ display:flex; align-items:center; gap:14px; padding:2px 0 18px 0; }}
  .fio {{ width:2px; height:46px; background:linear-gradient(180deg,{CHUMBO} 0%,{LATAO} 100%);
          position:relative; flex:none; }}
  .fio::after {{ content:""; position:absolute; bottom:-7px; left:-4px; width:10px; height:10px;
          background:{LATAO}; transform:rotate(45deg); }}
  .marca h1 {{ margin:0; font-size:1.55rem; font-weight:700; }}
  .marca span {{ display:block; font-family:'IBM Plex Mono',monospace; font-size:.68rem;
          letter-spacing:.22em; text-transform:uppercase; color:{CONCRETO}; margin-top:2px; }}
  /* cartao de indicador */
  .kpi {{ background:{GRAFITE}; border:1px solid {CHUMBO}; border-left:3px solid {CHUMBO};
          border-radius:3px; padding:14px 16px; height:100%; }}
  .kpi.ok {{ border-left-color:{APRUMADO}; }}
  .kpi.alerta {{ border-left-color:{LATAO}; }}
  .kpi.critico {{ border-left-color:{FORA}; }}
  .kpi .rot {{ font-family:'IBM Plex Mono',monospace; font-size:.63rem; letter-spacing:.16em;
          text-transform:uppercase; color:{CONCRETO}; }}
  .kpi .val {{ font-family:'IBM Plex Mono',monospace; font-size:1.72rem; font-weight:600;
          color:{GIZ}; line-height:1.35; }}
  .kpi .sub {{ font-size:.76rem; color:{CONCRETO}; }}
  /* titulo de secao com o fio a esquerda */
  .sec {{ font-family:'Archivo',sans-serif; font-size:1.02rem; font-weight:600;
          border-left:3px solid {LATAO}; padding:1px 0 1px 11px; margin:26px 0 12px 0; }}
  /* linha do tempo de eventos */
  .ev {{ background:{GRAFITE}; border:1px solid {CHUMBO}; border-left:3px solid {FORA};
         border-radius:3px; padding:11px 14px; margin-bottom:9px; }}
  .ev.resolucao {{ border-left-color:{APRUMADO}; }}
  .ev .quando {{ font-family:'IBM Plex Mono',monospace; font-size:.66rem; letter-spacing:.13em;
         text-transform:uppercase; color:{CONCRETO}; }}
  .ev .tit {{ font-weight:600; font-size:.93rem; margin:3px 0 4px 0; }}
  .ev .txt {{ font-size:.81rem; color:{CONCRETO}; line-height:1.5; }}
  .ev .acao {{ font-size:.79rem; color:{APRUMADO}; margin-top:6px; }}
  [data-testid="stDataFrame"] {{ border:1px solid {CHUMBO}; border-radius:3px; }}
  #MainMenu, footer {{ visibility:hidden; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------- dados
@st.cache_data(ttl=600)
def q(sql: str) -> pd.DataFrame:
    with sqlite3.connect(DB) as con:
        return pd.read_sql(sql, con)


def brl(v, casas=0):
    if pd.isna(v):
        return "—"
    if abs(v) >= 1e6:
        return f"R$ {v/1e6:,.2f} mi".replace(",", "@").replace(".", ",").replace("@", ".")
    return f"R$ {v:,.{casas}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def kpi(rotulo, valor, sub="", nivel=""):
    st.markdown(
        f'<div class="kpi {nivel}"><div class="rot">{rotulo}</div>'
        f'<div class="val">{valor}</div><div class="sub">{sub}</div></div>',
        unsafe_allow_html=True)


def sec(titulo):
    st.markdown(f'<div class="sec">{titulo}</div>', unsafe_allow_html=True)


def base_layout(fig, altura=380, legenda=True):
    fig.update_layout(
        height=altura, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans", color=CONCRETO, size=12),
        margin=dict(l=10, r=16, t=44, b=10), hovermode="x unified",
        showlegend=legenda,
        legend=dict(orientation="h", y=1.14, x=0, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=11)),
        title=dict(font=dict(family="Archivo", size=14, color=GIZ), x=0, xanchor="left"),
    )
    fig.update_xaxes(showgrid=False, linecolor=CHUMBO, tickfont=dict(size=11))
    fig.update_yaxes(gridcolor=CHUMBO, griddash="dot", zeroline=False, tickfont=dict(size=11))
    return fig


# ---------------------------------------------------------------- sidebar
st.sidebar.markdown(
    f'<div class="marca"><div class="fio"></div><div><h1>PRUMO</h1>'
    f'<span>Engenharia</span></div></div>', unsafe_allow_html=True)

pagina = st.sidebar.radio(
    "Painel", ["Portfólio", "Obra", "Suprimentos", "Segurança e Qualidade", "Comercial"],
    label_visibility="collapsed")

obras = q("SELECT * FROM dim_obra ORDER BY id_obra")
st.sidebar.markdown("---")
st.sidebar.caption(
    "Posição de agosto/2026.  \n"
    "Prumo Engenharia é uma empresa fictícia. Todos os dados são gerados por "
    "script e não têm relação com obra ou cliente real.")


# ================================================================ PORTFÓLIO
if pagina == "Portfólio":
    st.markdown(
        f'<div class="marca"><div class="fio"></div><div>'
        f'<h1>Painel de obras</h1><span>o que está fora de prumo</span></div></div>',
        unsafe_allow_html=True)

    resumo = q("""
        SELECT o.id_obra, o.nome_obra, o.cidade, o.status_obra, o.orcamento_previsto,
               SUM(c.custo_orcado)      AS orcado_ate_hoje,
               SUM(c.custo_realizado)   AS realizado
        FROM fato_custo c JOIN dim_obra o USING(id_obra)
        WHERE c.custo_realizado IS NOT NULL
        GROUP BY 1,2,3,4,5""")
    prazo = q("""
        SELECT id_obra,
               MAX(CASE WHEN avanco_real_acum IS NOT NULL THEN avanco_previsto_acum END) AS prev,
               MAX(avanco_real_acum) AS real
        FROM fato_avanco_fisico GROUP BY 1""")
    resumo = resumo.merge(prazo, on="id_obra")
    resumo["desvio_custo_pct"] = (resumo["realizado"] / resumo["orcado_ate_hoje"] - 1) * 100
    resumo["desvio_prazo_pp"] = (resumo["real"] - resumo["prev"]) * 100

    total_orc = resumo["orcado_ate_hoje"].sum()
    total_real = resumo["realizado"].sum()
    estouro = total_real - total_orc
    pior = resumo.loc[resumo["desvio_prazo_pp"].idxmin()]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Carteira em execução", brl(resumo["orcamento_previsto"].sum()),
            f"{len(resumo)} obras · 2 cidades")
    with c2:
        kpi("Estouro acumulado", brl(estouro),
            f"{estouro/total_orc*100:+.1f}% sobre o orçado até hoje", "critico")
    with c3:
        media_pp = resumo["desvio_prazo_pp"].mean()
        kpi("Desvio médio de prazo", f"{media_pp:+.1f} p.p.",
            "avanço real contra o planejado", "critico" if media_pp < -5 else "alerta")
    with c4:
        kpi("Maior atraso", f"{pior['desvio_prazo_pp']:+.1f} p.p.",
            pior["nome_obra"], "critico")

    sec("Custo e prazo lado a lado")
    st.caption("Cada obra falha de um jeito diferente. Olhar só uma das duas dimensões esconde metade do problema.")

    g1, g2 = st.columns([3, 2])
    with g1:
        d = resumo.sort_values("desvio_custo_pct")
        fig = go.Figure()
        fig.add_bar(y=d["nome_obra"], x=d["desvio_custo_pct"], orientation="h",
                    marker_color=[FORA if v > 5 else (LATAO if v > 0 else APRUMADO)
                                  for v in d["desvio_custo_pct"]],
                    text=[f"{v:+.1f}%" for v in d["desvio_custo_pct"]],
                    textposition="outside", textfont=dict(family="IBM Plex Mono", color=GIZ),
                    hovertemplate="%{y}<br>desvio de custo %{x:+.1f}%<extra></extra>")
        fig.add_vline(x=0, line_color=CHUMBO)
        fig.update_layout(title="Desvio de custo por obra")
        fig.update_xaxes(range=[min(d["desvio_custo_pct"].min() * 1.4, -2),
                                d["desvio_custo_pct"].max() * 1.45], ticksuffix="%")
        st.plotly_chart(base_layout(fig, 320, False), width="stretch")
    with g2:
        fig = go.Figure()
        for _, r in resumo.iterrows():
            fig.add_scatter(
                x=[r["desvio_prazo_pp"]], y=[r["desvio_custo_pct"]], mode="markers+text",
                marker=dict(size=r["orcamento_previsto"] / 6e5, color=LATAO,
                            line=dict(color=BREU, width=2), opacity=.85),
                text=[r["nome_obra"].split()[-1]], textposition="top center",
                textfont=dict(size=10, color=CONCRETO), name=r["nome_obra"],
                hovertemplate=f"<b>{r['nome_obra']}</b><br>prazo %{{x:+.1f}} p.p."
                              f"<br>custo %{{y:+.1f}}%<extra></extra>")
        fig.add_vline(x=0, line_color=CHUMBO)
        fig.add_hline(y=0, line_color=CHUMBO)
        fig.update_layout(title="Prazo × custo · tamanho = orçamento")
        fig.update_xaxes(title="desvio de prazo (p.p.)", ticksuffix=" p.p.")
        fig.update_yaxes(title="desvio de custo (%)", ticksuffix="%")
        st.plotly_chart(base_layout(fig, 320, False), width="stretch")

    sec("Quadro das obras")
    tab = resumo[["nome_obra", "cidade", "status_obra", "orcamento_previsto",
                  "realizado", "desvio_custo_pct", "desvio_prazo_pp"]].copy()
    tab.columns = ["Obra", "Cidade", "Status", "Orçamento", "Realizado",
                   "Desvio custo %", "Desvio prazo p.p."]
    st.dataframe(
        tab.style.format({"Orçamento": lambda v: brl(v), "Realizado": lambda v: brl(v),
                          "Desvio custo %": "{:+.1f}%", "Desvio prazo p.p.": "{:+.1f}"})
           .background_gradient(subset=["Desvio custo %"], cmap="Reds")
           .background_gradient(subset=["Desvio prazo p.p."], cmap="Reds_r"),
        width="stretch", hide_index=True)


# ================================================================ OBRA
elif pagina == "Obra":
    nome = st.sidebar.selectbox("Obra", obras["nome_obra"])
    o = obras[obras["nome_obra"] == nome].iloc[0]
    idb = int(o["id_obra"])

    st.markdown(f'<div class="marca"><div class="fio"></div><div><h1>{o["nome_obra"]}</h1>'
                f'<span>{o["cidade"]} · {o["tipo_obra"]} · {o["gerente_obra"]}</span>'
                f'</div></div>', unsafe_allow_html=True)

    av = q(f"SELECT * FROM fato_avanco_fisico WHERE id_obra={idb} ORDER BY id_tempo")
    cal = q("SELECT id_tempo, nome_mes FROM dim_calendario")
    av = av.merge(cal, on="id_tempo", how="left")
    cu = q(f"""SELECT ano_mes, SUM(custo_orcado) orc, SUM(custo_realizado) real
               FROM fato_custo WHERE id_obra={idb} GROUP BY 1 ORDER BY 1""")
    ev = q(f"SELECT * FROM fato_eventos WHERE id_obra={idb} ORDER BY ano_mes")
    real = av[av["avanco_real_acum"].notna()]
    ult = real.iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Avanço físico", f"{ult['avanco_real_acum']*100:.1f}%",
            f"planejado {ult['avanco_previsto_acum']*100:.1f}%")
    with c2:
        d = ult["desvio_prazo_pp"]
        kpi("Fora de prumo", f"{d:+.1f} p.p.", "real contra planejado",
            "critico" if d < -5 else ("alerta" if d < -1 else "ok"))
    with c3:
        orc, rea = cu["orc"].sum(), cu["real"].sum()
        dc = (rea / cu[cu['real'].notna()]['orc'].sum() - 1) * 100
        kpi("Desvio de custo", f"{dc:+.1f}%", f"{brl(rea)} realizados",
            "critico" if dc > 8 else ("alerta" if dc > 3 else "ok"))
    with c4:
        pior = real.loc[real["indice_produtividade"].idxmin()]
        kpi("Pior mês", f"{pior['indice_produtividade']:.2f}",
            f"índice de produtividade · {pior['nome_mes']}", "critico")

    sec("Curva S · o fio de prumo mede a distância entre o plano e a obra")

    fig = go.Figure()
    # o vao entre previsto e realizado, preenchido
    fig.add_scatter(x=av["nome_mes"], y=av["avanco_previsto_acum"] * 100, name="Planejado",
                    line=dict(color=ACO, width=2, dash="dot"),
                    hovertemplate="planejado %{y:.1f}%<extra></extra>")
    fig.add_scatter(x=real["nome_mes"], y=real["avanco_real_acum"] * 100, name="Realizado",
                    line=dict(color=LATAO, width=3), fill="tonexty",
                    fillcolor="rgba(214,90,78,0.13)",
                    hovertemplate="realizado %{y:.1f}%<extra></extra>")
    # fios de prumo: um segmento vertical por mes, do plano ate o real
    for _, r in real.iterrows():
        cor = APRUMADO if r["desvio_prazo_pp"] >= 0 else FORA
        fig.add_scatter(x=[r["nome_mes"], r["nome_mes"]],
                        y=[r["avanco_previsto_acum"] * 100, r["avanco_real_acum"] * 100],
                        mode="lines", line=dict(color=cor, width=1),
                        showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=[ult["nome_mes"]], y=[ult["avanco_real_acum"] * 100], mode="markers",
                    marker=dict(symbol="diamond", size=11, color=LATAO,
                                line=dict(color=BREU, width=2)),
                    showlegend=False, hoverinfo="skip")
    # eventos marcados no eixo
    for _, e in ev.iterrows():
        m = cal[cal["id_tempo"] == e["id_tempo"]]
        if m.empty:
            continue
        cor = APRUMADO if e["tipo"] == "resolucao" else FORA
        fig.add_vline(x=m.iloc[0]["nome_mes"], line=dict(color=cor, width=1, dash="dot"),
                      opacity=.55)
    fig.update_layout(title="Avanço físico acumulado (%)")
    fig.update_yaxes(ticksuffix="%", range=[0, 105])
    st.plotly_chart(base_layout(fig, 400), width="stretch")

    e1, e2 = st.columns([3, 2])
    with e1:
        fig = go.Figure()
        cores = [FORA if v < 0.8 else (APRUMADO if v > 1.05 else LATAO)
                 for v in real["indice_produtividade"]]
        fig.add_bar(x=real["nome_mes"], y=real["indice_produtividade"], marker_color=cores,
                    hovertemplate="índice %{y:.2f}<extra></extra>")
        fig.add_hline(y=1, line=dict(color=ACO, width=1, dash="dash"),
                      annotation_text="plano", annotation_font_color=CONCRETO)
        fig.update_layout(title="Índice de produtividade mensal · 1,00 = conforme o plano")
        st.plotly_chart(base_layout(fig, 300, False), width="stretch")
    with e2:
        cu2 = cu[cu["real"].notna()].copy()
        cu2["ac_orc"] = cu2["orc"].cumsum() / 1e6
        cu2["ac_real"] = cu2["real"].cumsum() / 1e6
        fig = go.Figure()
        fig.add_scatter(x=cu2["ano_mes"], y=cu2["ac_orc"], name="Orçado",
                        line=dict(color=ACO, width=2, dash="dot"))
        fig.add_scatter(x=cu2["ano_mes"], y=cu2["ac_real"], name="Realizado",
                        line=dict(color=FORA, width=3), fill="tonexty",
                        fillcolor="rgba(214,90,78,0.13)")
        fig.update_layout(title="Custo acumulado (R$ mi)")
        st.plotly_chart(base_layout(fig, 300), width="stretch")

    sec("Diário de bordo · o que derrubou e o que recuperou")
    col_dor, col_res = st.columns(2)
    for _, e in ev.iterrows():
        alvo = col_dor if e["tipo"] == "dor" else col_res
        classe = "ev" if e["tipo"] == "dor" else "ev resolucao"
        rot = "Dor" if e["tipo"] == "dor" else "Resolução"
        acao = f'<div class="acao">→ {e["acao"]}</div>' if e["acao"] else ""
        with alvo:
            st.markdown(
                f'<div class="{classe}"><div class="quando">{e["ano_mes"]} · '
                f'{e["categoria"]} · {rot}</div><div class="tit">{e["titulo"]}</div>'
                f'<div class="txt">{e["descricao"]}</div>{acao}</div>',
                unsafe_allow_html=True)

    sec("Onde o dinheiro vazou, por etapa")
    et = q(f"""SELECT e.nome_etapa, SUM(c.custo_orcado) orc, SUM(c.custo_realizado) real
               FROM fato_custo c JOIN dim_etapa e USING(id_etapa)
               WHERE c.id_obra={idb} AND c.custo_realizado IS NOT NULL
               GROUP BY 1 HAVING SUM(c.custo_orcado) > 0 ORDER BY e.id_etapa""")
    et["desvio"] = et["real"] - et["orc"]
    et = et.sort_values("desvio")
    fig = go.Figure()
    fig.add_bar(y=et["nome_etapa"], x=et["desvio"] / 1e3, orientation="h",
                marker_color=[FORA if v > 0 else APRUMADO for v in et["desvio"]],
                hovertemplate="%{y}<br>desvio R$ %{x:,.0f} mil<extra></extra>")
    fig.add_vline(x=0, line_color=CHUMBO)
    fig.update_layout(title="Desvio de custo por etapa (R$ mil)")
    st.plotly_chart(base_layout(fig, 380, False), width="stretch")


# ================================================================ SUPRIMENTOS
elif pagina == "Suprimentos":
    st.markdown('<div class="marca"><div class="fio"></div><div><h1>Suprimentos</h1>'
                '<span>saving, prazo de entrega e confiabilidade</span></div></div>',
                unsafe_allow_html=True)

    co = q("""SELECT c.*, f.nome_fornecedor, f.curva_abc, o.nome_obra
              FROM fato_compras c JOIN dim_fornecedor f USING(id_fornecedor)
              JOIN dim_obra o USING(id_obra)""")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Saving negociado", brl(co["saving_valor"].sum()),
            f"{co['saving_pct'].mean():.1f}% médio sobre o cotado", "ok")
    with c2:
        otif = co["entrega_otif"].mean() * 100
        kpi("OTIF", f"{otif:.1f}%", "entregas no prazo",
            "ok" if otif > 80 else "alerta")
    with c3:
        kpi("Lead time médio", f"{co['lead_time_real_dias'].mean():.0f} dias",
            f"previsto {co['lead_time_previsto_dias'].mean():.0f} dias")
    with c4:
        kpi("Pedidos", f"{len(co):,}".replace(",", "."), "no período analisado")

    sec("A crise do aço e o que a resolveu")
    st.caption("Agosto e setembro de 2025: fornecedor único de aço em ruptura. "
               "Compra no spot com saving negativo — pagou-se acima do cotado. "
               "Em outubro, um segundo fornecedor classe A entra e o indicador vira.")

    mes = co.groupby("ano_mes").agg(
        otif=("entrega_otif", "mean"), saving=("saving_pct", "mean"),
        lead=("lead_time_real_dias", "mean")).reset_index()
    g1, g2 = st.columns(2)
    with g1:
        fig = go.Figure()
        fig.add_bar(x=mes["ano_mes"], y=mes["otif"] * 100,
                    marker_color=[FORA if v < .7 else (LATAO if v < .8 else APRUMADO)
                                  for v in mes["otif"]],
                    hovertemplate="OTIF %{y:.0f}%<extra></extra>")
        fig.add_hline(y=85, line=dict(color=ACO, width=1, dash="dash"),
                      annotation_text="meta 85%", annotation_font_color=CONCRETO)
        fig.update_layout(title="OTIF mensal (%)")
        fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(base_layout(fig, 320, False), width="stretch")
    with g2:
        fig = go.Figure()
        fig.add_bar(x=mes["ano_mes"], y=mes["saving"],
                    marker_color=[FORA if v < 0 else APRUMADO for v in mes["saving"]],
                    hovertemplate="saving %{y:.1f}%<extra></extra>")
        fig.add_hline(y=0, line_color=CHUMBO)
        fig.update_layout(title="Saving médio mensal (%)")
        fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(base_layout(fig, 320, False), width="stretch")

    sec("Ranking de fornecedores")
    rank = co.groupby(["nome_fornecedor", "curva_abc"]).agg(
        pedidos=("id_pedido", "count"), comprado=("valor_comprado", "sum"),
        saving=("saving_pct", "mean"), otif=("entrega_otif", "mean"),
        atraso=("lead_time_real_dias", "mean")).reset_index()
    rank["otif"] *= 100
    rank = rank.sort_values("otif")
    rank.columns = ["Fornecedor", "Curva", "Pedidos", "Comprado", "Saving %", "OTIF %", "Lead time"]
    st.dataframe(
        rank.style.format({"Comprado": lambda v: brl(v), "Saving %": "{:.1f}%",
                           "OTIF %": "{:.0f}%", "Lead time": "{:.0f} d"})
            .background_gradient(subset=["OTIF %"], cmap="RdYlGn"),
        width="stretch", hide_index=True)


# ================================================== SEGURANÇA E QUALIDADE
elif pagina == "Segurança e Qualidade":
    st.markdown('<div class="marca"><div class="fio"></div><div>'
                '<h1>Segurança e qualidade</h1>'
                '<span>acidentes, retrabalho e o custo de fazer duas vezes</span>'
                '</div></div>', unsafe_allow_html=True)

    sg = q("""SELECT s.*, o.nome_obra FROM fato_seguranca s JOIN dim_obra o USING(id_obra)""")
    ql = q("""SELECT q.*, o.nome_obra FROM fato_qualidade q JOIN dim_obra o USING(id_obra)""")

    tf = sg["acidentes_com_afastamento"].sum() / sg["hht"].sum() * 1e6
    tg = sg["dias_perdidos"].sum() / sg["hht"].sum() * 1e6
    fvs = ql["aprovados_primeira"].sum() / ql["inspecoes_fvs"].sum() * 100

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Taxa de frequência", f"{tf:.1f}", "acidentes c/ afastamento por milhão de HHT",
            "alerta" if tf > 8 else "ok")
    with c2:
        kpi("Taxa de gravidade", f"{tg:.0f}", "dias perdidos por milhão de HHT", "critico")
    with c3:
        kpi("FVS aprovada de primeira", f"{fvs:.1f}%", "meta 90%",
            "alerta" if fvs < 90 else "ok")
    with c4:
        kpi("Custo de retrabalho", brl(ql["custo_retrabalho"].sum()),
            "serviço refeito no período", "critico")

    sec("Um acidente muda o gráfico inteiro")
    st.caption("Dezembro de 2025, fachada da Atlântica: queda de nível, obra interditada "
               "5 dias, 38 dias perdidos. O programa de proteção coletiva entra em fevereiro "
               "e zera os afastamentos nos seis meses seguintes.")

    m = sg.groupby("ano_mes").agg(ca=("acidentes_com_afastamento", "sum"),
                                  dias=("dias_perdidos", "sum"),
                                  hht=("hht", "sum")).reset_index()
    m["tf"] = m["ca"] / m["hht"] * 1e6
    g1, g2 = st.columns(2)
    with g1:
        fig = go.Figure()
        fig.add_bar(x=m["ano_mes"], y=m["dias"], marker_color=FORA,
                    hovertemplate="%{y} dias perdidos<extra></extra>")
        fig.update_layout(title="Dias perdidos por acidente")
        st.plotly_chart(base_layout(fig, 320, False), width="stretch")
    with g2:
        qm = ql.groupby("ano_mes").agg(insp=("inspecoes_fvs", "sum"),
                                       ok=("aprovados_primeira", "sum"),
                                       rt=("custo_retrabalho", "sum")).reset_index()
        qm["pct"] = qm["ok"] / qm["insp"] * 100
        fig = go.Figure()
        fig.add_bar(x=qm["ano_mes"], y=qm["rt"] / 1e3, name="Retrabalho (R$ mil)",
                    marker_color=CHUMBO)
        fig.add_scatter(x=qm["ano_mes"], y=qm["pct"], name="FVS 1ª vez (%)",
                        yaxis="y2", line=dict(color=LATAO, width=3))
        fig.update_layout(title="Retrabalho × aprovação na primeira inspeção",
                          yaxis2=dict(overlaying="y", side="right", range=[0, 100],
                                      ticksuffix="%", showgrid=False,
                                      tickfont=dict(color=CONCRETO, size=11)))
        st.plotly_chart(base_layout(fig, 320), width="stretch")

    sec("Retrabalho por obra e etapa")
    piv = ql.groupby(["nome_obra"]).agg(
        insp=("inspecoes_fvs", "sum"), rep=("reprovados", "sum"),
        custo=("custo_retrabalho", "sum"), perda=("perda_material_pct", "mean")).reset_index()
    piv["taxa"] = piv["rep"] / piv["insp"] * 100
    piv = piv[["nome_obra", "insp", "rep", "taxa", "custo", "perda"]]
    piv.columns = ["Obra", "Inspeções", "Reprovações", "Taxa reprovação %",
                   "Custo retrabalho", "Perda material %"]
    st.dataframe(
        piv.style.format({"Taxa reprovação %": "{:.1f}%", "Custo retrabalho": lambda v: brl(v),
                          "Perda material %": "{:.1f}%"})
           .background_gradient(subset=["Taxa reprovação %"], cmap="Reds"),
        width="stretch", hide_index=True)


# ================================================================ COMERCIAL
else:
    st.markdown('<div class="marca"><div class="fio"></div><div><h1>Comercial</h1>'
                '<span>velocidade de vendas, estoque e carteira</span></div></div>',
                unsafe_allow_html=True)

    vd = q("""SELECT v.*, o.nome_obra FROM fato_vendas v JOIN dim_obra o USING(id_obra)""")
    ult = vd.sort_values("ano_mes").groupby("nome_obra").tail(1)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("VGV vendido", brl(vd["vgv_vendido_mes"].sum()), "acumulado no período", "ok")
    with c2:
        kpi("VSO médio", f"{vd['vso_pct'].mean():.1f}%", "velocidade sobre oferta")
    with c3:
        kpi("Estoque", f"{int(ult['estoque_unidades'].sum())} un.",
            f"de {int(ult['unidades_totais'].sum())} lançadas")
    with c4:
        kpi("Distratos", f"{int(vd['distratos_mes'].sum())} un.",
            f"inadimplência média {vd['inadimplencia_pct'].mean():.1f}%", "alerta")

    sec("A obra na mídia respinga na venda")
    st.caption("O VSO da Atlântica cai pela metade no mês do acidente; o da Mata Atlântica, "
               "durante o embargo ambiental. Prazo e reputação são o mesmo indicador com atraso.")

    fig = go.Figure()
    cores = [LATAO, FORA, APRUMADO, ACO]
    for i, (nome, g) in enumerate(vd.groupby("nome_obra")):
        g = g.sort_values("ano_mes")
        fig.add_scatter(x=g["ano_mes"], y=g["vso_pct"], name=nome,
                        line=dict(color=cores[i % 4], width=2.5),
                        hovertemplate="%{y:.1f}%<extra></extra>")
    fig.update_layout(title="VSO mensal por obra (%)")
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(base_layout(fig, 380), width="stretch")

    sec("Estoque e carteira")
    tab = ult[["nome_obra", "unidades_totais", "unidades_vendidas_acum", "estoque_unidades",
               "ticket_medio", "inadimplencia_pct"]].copy()
    tab.columns = ["Obra", "Unidades", "Vendidas", "Estoque", "Ticket médio", "Inadimplência %"]
    st.dataframe(
        tab.style.format({"Ticket médio": lambda v: brl(v), "Inadimplência %": "{:.1f}%"}),
        width="stretch", hide_index=True)
