from __future__ import annotations

import pandas as pd
import requests
import sidrapy

# --------- mapas de UF ----------
UF_NAME_TO_SIGLA = {
    "Rondônia":"RO","Acre":"AC","Amazonas":"AM","Roraima":"RR","Pará":"PA","Amapá":"AP","Tocantins":"TO",
    "Maranhão":"MA","Piauí":"PI","Ceará":"CE","Rio Grande do Norte":"RN","Paraíba":"PB","Pernambuco":"PE",
    "Alagoas":"AL","Sergipe":"SE","Bahia":"BA","Minas Gerais":"MG","Espírito Santo":"ES","Rio de Janeiro":"RJ",
    "São Paulo":"SP","Paraná":"PR","Santa Catarina":"SC","Rio Grande do Sul":"RS","Mato Grosso do Sul":"MS",
    "Mato Grosso":"MT","Goiás":"GO","Distrito Federal":"DF"
}
UF_CODE_TO_SIGLA = {
    11:"RO",12:"AC",13:"AM",14:"RR",15:"PA",16:"AP",17:"TO",
    21:"MA",22:"PI",23:"CE",24:"RN",25:"PB",26:"PE",27:"AL",28:"SE",29:"BA",
    31:"MG",32:"ES",33:"RJ",35:"SP",
    41:"PR",42:"SC",43:"RS",
    50:"MS",51:"MT",52:"GO",53:"DF",
}
UF_SIGLAS = list(UF_NAME_TO_SIGLA.values())
SIGLA_TO_CODE = {v:k for k,v in UF_CODE_TO_SIGLA.items()}

HEADERS = {"User-Agent":"Mozilla/5.0","Accept":"application/json"}

# --------- utilidades ----------
def _parse_period_code(code: str):
    s = str(code)
    try:
        if len(s)==4 and s.isdigit():
            return pd.Timestamp(year=int(s), month=1, day=1)
        if len(s)==6 and s.isdigit():
            year, kk = int(s[:4]), int(s[4:])
            if 1 <= kk <= 4:                       # trimestral
                return pd.Timestamp(year=year, month={1:3,2:6,3:9,4:12}[kk], day=1)
            if 1 <= kk <= 12:                      # mensal
                return pd.Timestamp(year=year, month=kk, day=1)
            if kk in (1,2):                        # semestral
                return pd.Timestamp(year=year, month={1:6,2:12}[kk], day=1)
    except Exception:
        pass
    return pd.NaT

def _tidy(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for a,b in [("D1N","UF_nome"),("D1C","UF_codigo"),("D2C","periodo_cod"),
                ("D2N","periodo_rotulo"),("V","valor"),("MN","unidade"),("D3N","variavel")]:
        if a in df.columns: rename[a]=b
    df = df.rename(columns=rename)
    df["data"] = df["periodo_cod"].apply(_parse_period_code) if "periodo_cod" in df.columns else pd.NaT
    # cria sigla UF
    if "UF_nome" in df.columns:
        df["UF"] = df["UF_nome"].map(UF_NAME_TO_SIGLA).fillna(df["UF_nome"])
    elif "UF_codigo" in df.columns:
        def _to_sigla(x):
            try: return UF_CODE_TO_SIGLA.get(int(x))
            except Exception: return None
        df["UF"] = df["UF_codigo"].apply(_to_sigla)
    else:
        df["UF"] = pd.NA
    return df

# --------- fallback direto na API v3 (servicodados) ----------
def _fetch_v3(agregado: str, variavel: str, periodos: str, ufs: list[str] | None) -> pd.DataFrame:
    if not ufs:
        loc = "N3[all]"
    else:
        codes = [str(SIGLA_TO_CODE[u.upper()]) for u in ufs]
        loc = f"N3[{','.join(codes)}]"
    url = (f"https://servicodados.ibge.gov.br/api/v3/agregados/{agregado}"
           f"/periodos/{periodos}/variaveis/{variavel}?localidades={loc}&view=flat")
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    js = r.json()
    df = pd.DataFrame(js)
    return _tidy(df)

# --------- funções principais ----------
def fetch_pnadc_desocupacao_uf(periodos: str = "all", ufs: list[str] | None = None) -> pd.DataFrame:
    """
    PNADC — taxa de desocupação (%) por UF (agregado 4099, variável 4099).
    Tenta via sidrapy (apisidra). Se falhar (DNS/rede), usa servicodados (API v3).
    """
    try:
        raw = sidrapy.get_table(
            table_code="4099",
            territorial_level="3",        # N3 = UF
            ibge_territorial_code="all",
            variable="4099",
            period=periodos,
            header="n",
            format="pandas",
        )
        df = _tidy(raw)
    except Exception:
        df = _fetch_v3("4099", "4099", periodos, ufs)

    keep = [c for c in ["data","periodo_cod","periodo_rotulo","UF","valor","unidade"] if c in df.columns]
    out = df[keep] if keep else df
    # filtra UFs se pedido
    if ufs and "UF" in out.columns:
        out = out[out["UF"].isin([u.upper() for u in ufs])]
    return out.sort_values(["UF","data","periodo_cod"], na_position="last").reset_index(drop=True)

def fetch_custom(agregado: str, variavel: str | None, periodos: str = "all", ufs: list[str] | None = None) -> pd.DataFrame:
    """Consulta genérica por UF; com fallback para API v3."""
    try:
        raw = sidrapy.get_table(
            table_code=str(agregado),
            territorial_level="3",        # N3 = UF
            ibge_territorial_code="all",
            variable=str(variavel) if variavel else None,
            period=periodos,
            header="n",
            format="pandas",
        )
        df = _tidy(raw)
    except Exception:
        if not variavel:
            raise ValueError("Para o fallback v3 é necessário informar 'variavel'.")
        df = _fetch_v3(str(agregado), str(variavel), periodos, ufs)

    keep = [c for c in ["data","periodo_cod","periodo_rotulo","UF","valor","unidade","variavel"] if c in df.columns]
    out = df[keep] if keep else df
    if ufs and "UF" in out.columns:
        out = out[out["UF"].isin([u.upper() for u in ufs])]
    return out.sort_values(["UF","data","periodo_cod"], na_position="last").reset_index(drop=True)
