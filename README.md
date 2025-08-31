# Desemprego (%) por UF — IBGE/SIDRA (PNADC)

App **Streamlit** para visualizar a **taxa de desocupação** (PNADC) por **UF** ao longo do tempo.
Selecione as UFs e clique **Gerar gráfico**. O app mostra **tabela completa**, **gráfico** e permite **baixar CSV**.

**Acesse online:** [unemployment-indicators.streamlit.app](https://unemployment-indicators.streamlit.app/)

> As instruções a seguir destinam-se apenas aos usuários que desejam executar o projeto localmente.

## Requisitos

- Python 3.10+
- Internet para consultar a API do IBGE

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\Activate.ps1  # Windows (PowerShell)
pip install -r requirements.txt
```

## Como executar

```bash
  streamlit run streamlit_sidraapi.py
```

Abra o endereço exibido (normalmente `http://localhost:8501`).

## Como usar

1. No menu lateral, selecione uma ou mais **UFs** (vazio = todas).
2. Clique em **Gerar gráfico**.
3. Veja a **tabela completa** e o **gráfico temporal** (eixo `YYYY-Qx`).
4. Clique em **Baixar CSV** para exportar os dados.

