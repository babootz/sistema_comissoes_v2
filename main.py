# main.py
import streamlit as st
import pandas as pd
import datetime
import uuid
import os
from io import BytesIO

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

# ---------- CONFIGURAÇÃO DOS ARQUIVOS ---------- #
ARQUIVOS = {
    "vendas": "vendas.csv",
    "pagamentos": "pagamentos.csv",
    "logs": "logs.csv"
}

COLUNAS_PADRAO = {
    "vendas": ["id", "segurado", "placa", "data", "seguradora", "premio_liquido", "percentual", "comissao_caio", "status", "observacao"],
    "pagamentos": ["id", "id_venda", "valor_pago", "data_pagamento", "observacao"],
    "logs": ["data_hora", "tipo_acao", "id_venda", "descricao"]
}

def carregar_ou_criar(nome):
    arquivo = ARQUIVOS[nome]
    if os.path.exists(arquivo):
        df = pd.read_csv(arquivo)
    else:
        df = pd.DataFrame(columns=COLUNAS_PADRAO[nome])
        df.to_csv(arquivo, index=False)
    return df

vendas = carregar_ou_criar("vendas")
pagamentos = carregar_ou_criar("pagamentos")
logs = carregar_ou_criar("logs")

# ---------- FUNÇÃO PARA CALCULAR COMISSÃO ---------- #
def calcular_comissao_caio(premio, percentual):
    return premio * (percentual / 100)

# ---------- INTERFACE PRINCIPAL ---------- #
st.markdown("""
    <h2 style='text-align: center;'>📋 Cadastrar Nova Venda</h2>
""", unsafe_allow_html=True)

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
            "data": data.strftime("%d/%m/%Y"),  # salva como string dd/mm/aaaa
            "seguradora": seguradora,
            "premio_liquido": premio_liquido,
            "percentual": percentual,
            "comissao_caio": comissao_caio,
            "status": "Pendente",
            "observacao": observacao
        }
        vendas = pd.concat([vendas, pd.DataFrame([nova_venda])], ignore_index=True)
        logs = pd.concat([logs, pd.DataFrame.from_records([{
            "data_hora": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "tipo_acao": "Cadastro",
            "id_venda": nova_venda["id"],
            "descricao": f"Venda cadastrada para {segurado}"
        }])], ignore_index=True)
        vendas.to_csv(ARQUIVOS["vendas"], index=False)
        logs.to_csv(ARQUIVOS["logs"], index=False)
        st.success("Venda salva com sucesso!")
        st.experimental_rerun()

# ---------- EXCLUSÃO DE VENDAS ---------- #
for index, row in vendas.iterrows():
    with st.expander(f"{row['segurado']} - {row['placa']} | Status: {row['status']}"):
        st.write(f"Data: {row['data']} | Seguradora: {row['seguradora']}")
        st.write(f"Prêmio Líquido: R${row['premio_liquido']:.2f} | % Comissão: {row['percentual']}%")
        st.write(f"Comissão Caio: R${row['comissao_caio']:.2f}")
        st.write(f"Observações: {row['observacao']}")

        excluir_btn = st.button("🗑️ Excluir Venda", key=f"excluir_{index}")
        if excluir_btn:
            # Confirmação simples
            confirmar = st.checkbox("Confirmar exclusão", key=f"confirmar_{index}")
            if confirmar:
                vendas = vendas.drop(index).reset_index(drop=True)
                pagamentos = pagamentos[pagamentos['id_venda'] != row['id']]
                logs = pd.concat([logs, pd.DataFrame.from_records([{
                    "data_hora": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "tipo_acao": "Exclusão",
                    "id_venda": row['id'],
                    "descricao": f"Venda excluída ({row['segurado']})"
                }])], ignore_index=True)
                vendas.to_csv(ARQUIVOS["vendas"], index=False)
                pagamentos.to_csv(ARQUIVOS["pagamentos"], index=False)
                logs.to_csv(ARQUIVOS["logs"], index=False)
                st.success("Venda excluída com sucesso!")
                st.experimental_rerun()

# ---------- EXPORTAÇÃO PARA EXCEL ---------- #
if st.button("Baixar Dashboard como Excel"):
    output_excel = vendas.copy()
    # a coluna data já está string no formato dd/mm/aaaa, converta para datetime para o Excel
    output_excel['data'] = pd.to_datetime(output_excel['data'], dayfirst=True, errors='coerce')
    output_excel['Data'] = output_excel['data'].dt.strftime('%d/%m/%Y')
    output_excel = output_excel.drop(columns=['data'])

    # Gerar Excel em memória para download
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        output_excel.to_excel(writer, index=False)
    buffer.seek(0)

    st.download_button(
        label="Download Excel",
        data=buffer,
        file_name="dashboard_comissoes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ---------- LOGS ---------- #
st.markdown("<h2 style='color: #2c3e50;'>📜 LOGS</h2>", unsafe_allow_html=True)
st.dataframe(logs.sort_values("data_hora", ascending=False), use_container_width=True)
st.caption("Atualizado em: " + datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
