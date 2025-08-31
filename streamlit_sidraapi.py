import streamlit as st
import altair as alt
import pandas as pd

from src.sidra_client_sidrapy import (
    fetch_pnadc_desocupacao_uf,
    UF_SIGLAS,
)

st.set_page_config(page_title="Desemprego (%) por UF — IBGE/SIDRA (PNADC)", layout="wide")
st.title("Desemprego (%) por UF — IBGE/SIDRA (PNADC)")

# --------- helpers ---------
def _periodo_label(df: pd.DataFrame) -> pd.DataFrame:
    """Cria rótulo amigável do tempo (YYYY-Qx / YYYY-MM / YYYY)."""
    if "data" not in df.columns or df["data"].isna().all():
        df["periodo_label"] = df.get("periodo_rotulo", "")
        return df
    m = df["data"].dt.month
    if m.isin([3, 6, 9, 12]).all():  # trimestral
        q = ((m - 1) // 3 + 1).astype("Int64")
        df["periodo_label"] = df["data"].dt.year.astype(str) + "-Q" + q.astype(str)
    elif (m >= 1).all():            # mensal (não deve ocorrer na PNADC trimestral, mas fica robusto)
        df["periodo_label"] = df["data"].dt.strftime("%Y-%m")
    else:                           # anual
        df["periodo_label"] = df["data"].dt.strftime("%Y")
    return df

def _filter_ufs(df: pd.DataFrame, ufs: list[str]) -> pd.DataFrame:
    if not ufs or "UF" not in df.columns:
        return df
    return df[df["UF"].isin(ufs)].copy()

@st.cache_data(show_spinner=False, ttl=60*30)
def _carregar(ufs_tuple: tuple[str, ...]) -> pd.DataFrame:
    # período fixo: "all"
    ufs = list(ufs_tuple)
    return fetch_pnadc_desocupacao_uf("all", ufs=ufs if ufs else None)

# --------- sidebar ---------
with st.sidebar:
    st.subheader("Selecione as UFs")
    ufs = st.multiselect("UFs (vazio = todas)", options=UF_SIGLAS, default=["PE", "SP", "RJ"])
    gerar = st.button("Gerar gráfico", type="primary")

# --------- execução ---------
if gerar:
    with st.spinner("Consultando o IBGE/SIDRA…"):
        df = _carregar(tuple(sorted(ufs)))
        df = _filter_ufs(df, ufs)

    if df.empty:
        st.warning("Sem dados para as UFs escolhidas.")
    else:
        df = _periodo_label(df)

        # --- TABELA COMPLETA ---
        # ordena por UF e tempo para exibição
        sort_cols = []
        if "UF" in df.columns: sort_cols.append("UF")
        if "data" in df.columns: sort_cols.append("data")
        if "periodo_cod" in df.columns: sort_cols.append("periodo_cod")
        if not sort_cols: sort_cols = [c for c in ["UF", "periodo_label"] if c in df.columns]
        df_table = df.sort_values(sort_cols)

        st.success(f"{len(df_table)} linhas • UFs: {', '.join(sorted(df_table['UF'].unique()))}")
        st.dataframe(df_table, use_container_width=True, height=360)
        st.caption("Tabela completa (todas as linhas).")

        # --- GRÁFICO ---
        y_label = (
            df["unidade"].dropna().iloc[0]
            if "unidade" in df.columns and df["unidade"].notna().any()
            else "%"
        )

        chart = (
            alt.Chart(df)
            .mark_line(point=True)
            .encode(
                x=alt.X("periodo_label:N", title="Período"),
                y=alt.Y("valor:Q", title=y_label),
                color="UF:N",
                tooltip=[c for c in ["UF", "periodo_label", "valor", "unidade"] if c in df.columns],
            )
            .properties(height=420)
        )
        st.altair_chart(chart, use_container_width=True)

        st.download_button(
            "Baixar CSV",
            df_table.to_csv(index=False).encode("utf-8"),
            "desemprego_pnadc_uf.csv",
            "text/csv",
        )
else:
    st.info("Escolha as UFs e clique em **Gerar gráfico**.")
