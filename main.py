# app.py
import streamlit as st
import pandas as pd
import datetime
import uuid
import os

# ---------- CONFIGURAÇÃO INICIAL ---------- #
st.set_page_config(page_title="Gerenciamento de Comissões", layout="wide", page_icon="🔐")

st.markdown("""
    <style>
        body {
            background-color: #121212;
            color: #ffffff;
        }
        .main {background-color: #1e1e1e;}
        div.block-container {padding-top: 2rem; padding-bottom: 2rem;}
        h1, h2, h3, h4 {color: #ffffff;}
        .stButton>button {background-color: #4CAF50; color: white;}
        .stTextInput>div>input {background-color: #2e2e2e; color: white;}
        .stTextInput>div>input:focus {background-color: #3e3e3e;}
    </style>
""", unsafe_allow_html=True)

# ---------- FUNÇÃO DE LOGIN ---------- #
login_senha = "0000"
login_status = False

st.markdown("""
    <h1 style='text-align: center;'>🔐 GERENCIAMENTO DE COMISSÕES</h1>
    <p style='text-align: center; font-size: 18px;'>Acesso restrito</p>
""", unsafe_allow_html=True)
senha = st.text_input("Digite a senha para acessar o sistema:", type="password")
if senha == login_senha:
    login_status = True

if not login_status:
    st.stop()

# ---------- FUNÇÕES DE CARREGAMENTO DE ARQUIVOS ---------- #
ARQUIVOS = {
    "vendas": "vendas.csv",
    "pagamentos": "pagamentos.csv",
    "logs": "logs.csv"
}

def carregar_arquivo(nome):
    if os.path.exists(ARQUIVOS[nome]):
        df = pd.read_csv(ARQUIVOS[nome])
        return df, None
    else:
        return pd.DataFrame(), None

# ---------- CARREGAR DADOS ---------- #
vendas, _ = carregar_arquivo("vendas")
pagamentos, _ = carregar_arquivo("pagamentos")
logs, _ = carregar_arquivo("logs")

if vendas.empty:
    vendas = pd.DataFrame(columns=["id", "segurado", "placa", "data", "seguradora", "premio_liquido", "percentual", "comissao_caio", "status", "observacao"])
if pagamentos.empty:
    pagamentos = pd.DataFrame(columns=["id", "id_venda", "valor_pago", "data_pagamento", "observacao"])
if logs.empty:
    logs = pd.DataFrame(columns=["data_hora", "tipo_acao", "id_venda", "descricao"])

# ---------- INTERFACE PRINCIPAL ---------- #
st.markdown("""
    <h2 style='text-align: center;'>📋 Cadastrar Nova Venda</h2>
""", unsafe_allow_html=True)

def calcular_comissao_caio(valor, percentual):
    return round((valor * percentual / 100), 2)

with st.form("nova_venda"):
    col1, col2, col3 = st.columns(3)
    segurado = col1.text_input("Segurado")
    placa = col2.text_input("Placa")
    data = col3.date_input("Data da Venda", value=datetime.date.today())

    col4, col5 = st.columns(2)
    seguradora = col4.text_input("Seguradora")
    premio_liquido = col5.number_input("Prêmio Líquido", min_value=0.0, step=0.01)

    percentual = st.number_input("% de Comissão", min_value=0.0, max_value=100.0, step=0.01)
    observacao = st.text_input("Observações")

    submitted = st.form_submit_button("Salvar Venda")
    if submitted and segurado:
        comissao_caio = calcular_comissao_caio(premio_liquido, percentual)
        nova_venda = {
            "id": str(uuid.uuid4()),
            "segurado": segurado,
            "placa": placa,
            "data": data.strftime("%d/%m/%Y"),
            "seguradora": seguradora,
            "premio_liquido": premio_liquido,
            "percentual": percentual,
            "comissao_caio": comissao_caio,
            "status": "Pendente",
            "observacao": observacao
        }
        vendas = pd.concat([vendas, pd.DataFrame([nova_venda])], ignore_index=True)
        logs = pd.concat([logs, pd.DataFrame.from_records([{
            "data_hora": datetime.datetime.now(),
            "tipo_acao": "Cadastro",
            "id_venda": nova_venda["id"],
            "descricao": f"Venda cadastrada para {segurado}"
        }])], ignore_index=True)
        vendas.to_csv(ARQUIVOS["vendas"], index=False)
        logs.to_csv(ARQUIVOS["logs"], index=False)
        st.success("Venda salva com sucesso!")

# ---------- EXCLUSÃO DE VENDAS ---------- #
for index, row in vendas.iterrows():
    with st.expander(f"{row['segurado']} - {row['placa']} | Status: {row['status']}"):
        st.write(f"Data: {row['data']} | Seguradora: {row['seguradora']}")
        st.write(f"Prêmio Líquido: R${row['premio_liquido']:.2f} | % Comissão: {row['percentual']}%")
        st.write(f"Comissão Caio: R${row['comissao_caio']:.2f}")
        st.write(f"Observações: {row['observacao']}")

        if st.button("🗑️ Excluir Venda", key=f"excluir_{index}"):
            confirmar = st.radio(
                f"Tem certeza que deseja excluir esta venda de {row['segurado']}?",
                ["Não", "Sim"],
                key=f"confirmar_excluir_{index}"
            )
            if confirmar == "Sim":
                vendas = vendas.drop(index)
                pagamentos = pagamentos[pagamentos['id_venda'] != row['id']]
                logs = pd.concat([logs, pd.DataFrame.from_records([{
                    "data_hora": datetime.datetime.now(),
                    "tipo_acao": "Exclusão",
                    "id_venda": row['id'],
                    "descricao": f"Venda excluída ({row['segurado']})"
                }])], ignore_index=True)
                vendas.to_csv(ARQUIVOS["vendas"], index=False)
                pagamentos.to_csv(ARQUIVOS["pagamentos"], index=False)
                logs.to_csv(ARQUIVOS["logs"], index=False)
                st.success("Venda excluída com sucesso")

# ---------- EXPORTAÇÃO PARA EXCEL ---------- #
if st.button("Baixar Dashboard como Excel"):
    output_excel = vendas.copy()
    output_excel.to_excel("dashboard_comissoes.xlsx", index=False)
    st.success("Arquivo Excel gerado com sucesso!")
    st.download_button(
        label="Download Excel",
        data=output_excel.to_excel(index=False),
        file_name="dashboard_comissoes.xlsx",
        mime="application/vnd.ms-excel"
    )

# ---------- LOGS ---------- #
st.markdown("<h2 style='color: #2c3e50;'>📜 LOGS</h2>", unsafe_allow_html=True)
st.dataframe(logs.sort_values("data_hora", ascending=False), use_container_width=True)
st.caption("Atualizado em: " + datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
