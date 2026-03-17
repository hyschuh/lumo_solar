import streamlit as st
import base64
import os
import re
import math
import pdfplumber
import pandas as pd

# 1. SEÇÃO 0 = VARIÁVEIS INICIAIS
#__________________________________________________________________________________

# 1. Configuração da Página
st.set_page_config(page_title="Lumo Energia", page_icon="☀️", layout="centered")

if 'representante_v' not in st.session_state:
    st.session_state.representante_v = True

# --- LÓGICA DE NAVEGAÇÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'formulario'


# --- LÓGICA DE NAVEGAÇÃO ---
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'formulario'
def ir_para_proxima():

    modos_especiais = ["Off-Grid", "Hibrido", "Microinversor", "Grid-Zero", "Ampliação"]
    telhados_especiais = ["Laje", "Solo", "Kalheta"]

    modo_usina = st.session_state.get('modo_usina_key')
    tipo_telhado = st.session_state.get('tipo_telhado_key')
    orc_manual = st.session_state.get('orc_man_key')

    if orc_manual or (modo_usina in modos_especiais) or (tipo_telhado in telhados_especiais):
        st.session_state.pagina = 'coleta_especifica'
    else:
        st.session_state.pagina = 'proxima_etapa'

def voltar():
    st.session_state.pagina = 'formulario'


# SEÇÃO 2  = FUNÇÃO DE PROCESSAMENTO DE PDF ---
def processar_fatura_pdf(arquivo_pdf):
    ordem_meses = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
    maiores_valores = {m: 0.0 for m in ordem_meses}
    regex_normal = r'(' + '|'.join(ordem_meses) + r')\s?\d{2}'
    meses_espacados = ['\s'.join(list(m)) for m in ordem_meses]
    regex_espacado = r'(' + '|'.join(meses_espacados) + r')\s?\d\s\d'
    filtro_final = re.compile(f'({regex_normal}|{regex_espacado})', re.IGNORECASE)
    try:
        with pdfplumber.open(arquivo_pdf) as pdf:
            for pagina in pdf.pages:
                palavras = pagina.extract_words(y_tolerance=3, x_tolerance=3)
                if not palavras: continue
                palavras_ordenadas = sorted(palavras, key=lambda x: (x['top'], x['x0']))
                linha_atual_y = palavras_ordenadas[0]['top']
                palavras_da_linha = []
                for p in palavras_ordenadas:
                    if abs(p['top'] - linha_atual_y) > 3:
                        frase = " ".join(palavras_da_linha)
                        match = filtro_final.search(frase)
                        if match:
                            frase_focada = frase[match.start():]
                            mes_chave = ""
                            for m in ordem_meses:
                                m_esp = ' '.join(list(m))
                                if frase_focada.upper().startswith(m_esp) or frase_focada.upper().startswith(m):
                                    mes_chave = m
                                    sub_regex = m_esp.replace(" ", r"\s?")
                                    frase_focada = re.sub(f'^{sub_regex}', '', frase_focada, flags=re.IGNORECASE)
                                    break
                            frase_focada = re.sub(r'^\s?\d\s?\d', '', frase_focada)
                            frase_focada = re.sub(r'\d*[\/,\-–—]\d*', '', frase_focada)
                            so_numeros = re.sub(r'[^0-9]', '', frase_focada)
                            if len(so_numeros) > 2:
                                valor_final = int(so_numeros[:-2])
                                if valor_final > maiores_valores[mes_chave]:
                                    maiores_valores[mes_chave] = valor_final
                        palavras_da_linha = [p['text']]
                        linha_atual_y = p['top']
                    else:
                        palavras_da_linha.append(p['text'])
        valores_reais = [v for v in maiores_valores.values() if v > 0]
        media = sum(valores_reais) / len(valores_reais) if valores_reais else 0.0
        return float(round(media)), maiores_valores
    except:
        return 0.0, {m: 0.0 for m in ordem_meses}


def get_base64(fp):
    if os.path.exists(fp):
        with open(fp, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# SEÇÃO 3 = ESTÉTICA DA PÁGINA
#_________________________________________________________________

bg_64 = get_base64(r"background.jpg")
logo_64 = get_base64(r"logo.jpg")

# --- ESTILIZAÇÃO CSS COMPLETA ---
st.markdown(f"""
    <style>
    [data-testid="stHeader"] {{ visibility: hidden; display: none; }}
    .block-container {{ padding-top: 2rem; }}
    .stApp {{ background: transparent; }}
    .stApp::before {{
        content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-image: url("data:image/jpg;base64,{bg_64 if bg_64 else ''}");
        background-size: cover; background-position: center; z-index: -2;
    }}
    .stApp::after {{ 
        content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 45, 114, 0.85); z-index: -1; 
    }}
    [data-testid="stExpander"] {{ background-color: transparent !important; border: 1px solid #ffa500 !important; border-radius: 10px !important; }}
    summary {{ background-color: #ffa500 !important; color: white !important; border-radius: 8px 8px 0px 0px !important; }}
    summary span p {{ color: white !important; font-weight: bold !important; font-size: 18px !important; }}
    summary svg {{ fill: white !important; }}
    .section-header {{ color: #ffa500; font-size: 20px; font-weight: bold; margin-top: 25px; margin-bottom: 10px; text-transform: uppercase; }}
    label p, .stCheckbox label span, .stRadio label span {{ color: white !important; font-weight: bold !important; }}
    .warning-text {{ color: #ff4b4b; font-size: 14px; font-weight: bold; }}

    .stButton>button {{
        width: 100%; background-color: #ffa500 !important; color: white !important;
        font-weight: bold !important; border: none !important; padding: 12px !important;
        border-radius: 10px !important; margin-top: 20px;
    }}

    [data-testid="stNumberInput"] div[data-baseweb="input"] {{
        background-color: white !important; border-radius: 8px !important; height: 45px !important;
    }}
    [data-testid="stNumberInput"] input {{
        color: black !important; -webkit-text-fill-color: black !important;
        font-size: 18px !important; font-weight: 500 !important;
    }}
    [data-testid="stNumberInput"] button {{ display: none !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO ---

if st.session_state.pagina == 'formulario':
    if logo_64:
        st.markdown(f'<div style="text-align: center;"><img src="data:image/jpg;base64,{logo_64}" width="220"></div>',
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

# SEÇÃO 4 = DADOS DO CLIENTE
#______________________________________________________________________________________-


    with st.expander("DADOS DO CLIENTE", expanded=True):
        st.text_input("Nome do Cliente", key='nome_cliente_key')  # KEY ADICIONADA
        atendimento_local = st.checkbox("Atendimento em Santa Cruz do Sul / Vera Cruz", value=True)
        if not atendimento_local:
            col_cid1, col_cid2 = st.columns([2, 1])
            with col_cid1: st.text_input("Cidade", key='cidade_key')
            with col_cid2: st.number_input("Distância (km)", min_value=0.0, key='distancia_key')

    st.markdown('<p class="section-header">DADOS DA INSTALAÇÃO</p>', unsafe_allow_html=True)
    col_inst1, col_inst2 = st.columns(2)
    with col_inst1:
        tipo_telhado = st.selectbox(
            "Estrutura/Telhado",
            ["Fibrocimento", "Metálico", "Telha", "Laje", "Solo", "Kalheta"],
            key='tipo_telhado_key'
        )
        if tipo_telhado in ["Laje", "Solo", "Kalheta"]:
            st.markdown('<span class="warning-text">Mais a baixo deverá ser informado o valor da estrutura</span>',
                        unsafe_allow_html=True)
    with col_inst2:
        st.selectbox("Tipo de Entrada", ["Monofásica", "Bifásica", "Trifásica"], key='entrada_key')


# SEÇÃO 5 = LEITURA DE PDF OU INSERIR MANUALMENTE O CONSUMO.
    #__________________________________________________________________________________________________________

    st.markdown('<p class="section-header">CONSUMO DE ENERGIA</p>', unsafe_allow_html=True)
    metodo_c = st.radio("Método de Entrada", ["Manual", "Leitura de PDF"], horizontal=True, key='metodo_consumo_key')

    consumo_base = 0.0

    if metodo_c == "Leitura de PDF":
        arquivo_pdf = st.file_uploader("Arraste o PDF aqui", type=["pdf"], key='pdf_uploader_key')
        if arquivo_pdf:
            consumo_base, historico_pdf = processar_fatura_pdf(arquivo_pdf)
            # SALVANDO NO ESTADO
            st.session_state['consumo_final_key'] = consumo_base
            st.session_state['historico_12_meses_key'] = historico_pdf
            st.markdown(f'<p style="color: white; font-weight: bold;">Média: {consumo_base:.0f} kWh</p>',
                        unsafe_allow_html=True)
    else:
        tipo_m = st.selectbox("Formato", ["Média Direta", "Histórico 12 Meses"], key='formato_consumo_key')
        if tipo_m == "Média Direta":
            consumo_base = st.number_input("Consumo Médio (kWh)", min_value=0.0, value=None, placeholder="0",
                                           key='consumo_direto_key')
            if consumo_base:
                st.session_state['consumo_final_key'] = consumo_base
        else:
            s_c, contagem = 0.0, 0
            dados_historico = {}
            for m in ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]:
                v = st.number_input(f"Mês de {m}", min_value=0.0, key=f"hist_{m}", value=None, placeholder="0")
                if v:
                    s_c += v
                    contagem += 1
                    dados_historico[m] = v

            consumo_base = s_c / contagem if contagem > 0 else 0.0
            # SALVANDO NO ESTADO
            st.session_state['consumo_final_key'] = consumo_base
            st.session_state['historico_12_meses_key'] = dados_historico
            st.markdown(f'<p style="color: white; font-weight: bold;">Média Calculada: {consumo_base:.1f} kWh</p>',
                        unsafe_allow_html=True)

# --- SEÇÃO 6: CONFIGURAÇÕES ADICIONAIS ---
st.markdown('<p class="section-header">CONFIGURAÇÕES ADICIONAIS</p>', unsafe_allow_html=True)

col_check1, col_check2 = st.columns(2)

with col_check1:
    # 1. Cliente Rural
    cliente_rural = st.checkbox("Cliente Rural", key='cliente_rural_key')

    # 2. Indicador
    indicador = st.checkbox("Indicador", key='indicador_key')
    if indicador:
        tipo_indicador = st.radio("Tipo de Indicador", ["Porcentagem", "Valor"], horizontal=True, key='tipo_indicador_key')
        if tipo_indicador == "Porcentagem":
            st.number_input("Porcentagem (%)", min_value=0.0, step=0.1, key='pc_indicador_key')
        else:
            st.number_input("Valor (R$)", min_value=0.0, step=50.0, key='valor_indicador_key')

    # 5. Representante (Novo com trava de senha)
    check_rep = st.checkbox("Representante", value=st.session_state.representante_v, key='rep_check_ui')

    if st.session_state.representante_v and not check_rep:
        senha = st.text_input("Digite a senha para desmarcar:", type="password", key='senha_rep_key')
        if senha == "0502":
            st.session_state.representante_v = False
            st.rerun()
        elif senha != "":
            st.error("Senha incorreta!")
    elif not st.session_state.representante_v and check_rep:
        st.session_state.representante_v = True
        st.rerun()

with col_check2:
    # 3. Sobra de Inversor
    sobra_inversor = st.checkbox("Sobra de Inversor", key='sobra_inv_key')
    if sobra_inversor:
        st.number_input("Porcentagem de Sobra de Inversor (%)", min_value=0.0, step=1.0, key='pc_sobra_inv_key')

    # 4. Sobra de Geração
    sobra_geracao = st.checkbox("Sobra de Geração", key='sobra_geracao_key')
    if sobra_geracao:
        tipo_sobra = st.radio("Tipo de Sobra", ["Porcentagem", "kWh"], horizontal=True, key='tipo_sobra_key')
        if tipo_sobra == "Porcentagem":
            st.number_input("Sobra em Porcentagem (%)", min_value=0.0, step=1.0, key='pc_sobra_geracao_key')
        else:
            st.number_input("Sobra em kWh", min_value=0.0, step=1.0, key='kwh_sobra_geracao_key')

# --- SEÇÃO 7: TIPO DE USINA ---
st.markdown('<p class="section-header">TIPO DE USINA</p>', unsafe_allow_html=True)

tipo_usina = st.selectbox(
    "Tipo de Usina",
    ["On-Grid", "Off-Grid", "Ampliação", "Microinversor", "Grid-Zero", "Híbrido"],
    key='modo_usina_key'
)

# Lógica de trava: Se não for On-Grid, o valor é forçado para True e o campo fica desabilitado
if tipo_usina != "On-Grid":
    st.checkbox("Modo Manual", value=True, key='orc_man_disabled', disabled=True)
    st.session_state.orc_man_key = True  # Garante que o estado interno acompanhe a trava
else:
    # Se for On-Grid, o usuário tem liberdade para marcar ou desmarcar
    st.checkbox("Modo Manual", key='orc_man_key')

# --- SEÇÃO 8: SELEÇÃO DE MARCA ---
st.markdown('<p class="section-header">SELEÇÃO DE MARCA</p>', unsafe_allow_html=True)

try:
    # Lendo a planilha de Inversores
    df_inversores = pd.read_excel(r"precos_lumo.xlsx", sheet_name="Inversores")

    # Extraindo marcas únicas (Coluna A - índice 0)
    marcas_disponiveis = df_inversores.iloc[:, 0].dropna().unique().tolist()

    # Verifica se o modo manual está ativo (considerando as duas chaves possíveis da lógica anterior)
    modo_manual_ativo = st.session_state.get('orc_man_key') or st.session_state.get('orc_man_disabled')

    if modo_manual_ativo:
        col_marca, col_potencia = st.columns(2)

        with col_marca:
            marca_selecionada = st.selectbox("Marca", options=marcas_disponiveis, key='marca_key')

        with col_potencia:
            # Filtrando potências (Coluna B - índice 1) baseadas na marca selecionada (Coluna A)
            potencias_filtradas = df_inversores[df_inversores.iloc[:, 0] == marca_selecionada].iloc[:,
                                  1].dropna().unique().tolist()
            st.selectbox("Potência", options=potencias_filtradas, key='potencia_key')

        # --- CAMPO ADICIONADO: QUANTIDADE DE INVERSORES ---
        st.number_input("Quantidade de Inversores", min_value=1, step=1, key='qtd_inversores_manual_key')

    else:
        # Se não for manual, exibe apenas a marca em largura total
        st.selectbox("Marca", options=marcas_disponiveis, key='marca_key')

except Exception as e:
    st.error(f"Erro ao carregar dados do arquivo Excel: {e}")


# --- SEÇÃO 9: DIMENSIONAMENTO DE USINA ---

# 1. Recupera os dados da Seção 5 e 6 com tratamento de erro (Garante que sejam números)
try:
    consumo_base_calculo = float(st.session_state.get('consumo_final_key', 0.0))
except:
    consumo_base_calculo = 0.0

# 2. Lógica da Sobra de Geração (Corrigindo a soma)
valor_sobra = 0.0
detalhe_sobra = "Sem sobra adicional"

if st.session_state.get('sobra_geracao_key'):
    tipo_sobra = st.session_state.get('tipo_sobra_key')

    if tipo_sobra == "Porcentagem":
        porcentagem = float(st.session_state.get('pc_sobra_geracao_key', 0.0))
        valor_sobra = consumo_base_calculo * (porcentagem / 100)
        detalhe_sobra = f"{porcentagem}% de sobra"
    else:
        valor_sobra = float(st.session_state.get('kwh_sobra_geracao_key', 0.0))
        detalhe_sobra = f"{valor_sobra} kWh de sobra fixa"

consumo_total_projeto = consumo_base_calculo + valor_sobra
st.session_state['consumo_total_projeto'] = consumo_total_projeto

# 4. Lógica do Módulo (Corrigindo o sumiço do checkbox)
modo_manual_geral = st.session_state.get('orc_man_key') or st.session_state.get('orc_man_disabled')
potencia_final = 0

# O checkbox deve aparecer sempre que o Modo Manual estiver ativo
if modo_manual_geral:
    definir_modulo_manual = st.checkbox("Definir módulo manualmente", key='def_modulo_man_key')

    if definir_modulo_manual:
        potencia_final = st.number_input("Potência do módulo (W)", min_value=0, step=5, format="%d",
                                         key='potencia_modulo_manual_key')
    else:
        # Se manual ativo, mas checkbox desmarcado -> busca na planilha
        buscar_na_planilha = True
else:
    buscar_na_planilha = True
    definir_modulo_manual = False

# 5. Busca na Planilha (Se não for inserção manual)
if not definir_modulo_manual:
    try:
        marca_selecionada = st.session_state.get('marca_key')
        if marca_selecionada:
            df_modulo = pd.read_excel(r"precos_lumo.xlsx", sheet_name="Módulo")
            filtro_modulo = df_modulo[df_modulo.iloc[:, 0] == marca_selecionada]
            if not filtro_modulo.empty:
                potencia_final = filtro_modulo.iloc[0, 1]
                st.markdown(
                    f'<p style="color: white; font-weight: bold;">Potência do Módulo ({marca_selecionada}): {potencia_final} W</p>',
                    unsafe_allow_html=True)
        else:
            st.info("Selecione uma marca para definir a potência do módulo.")
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")

st.session_state['potencia_modulo_final'] = potencia_final

# 6. Dimensionamento Final e Exibição Lado a Lado
if potencia_final > 0:
    # Lógica da Fórmula: ((Consumo Total / Potência do Módulo) * 10,2)
    razao_consumo_potencia = consumo_total_projeto / potencia_final
    resultado_bruto = razao_consumo_potencia * 10.2
    qtd_modulos = math.ceil(resultado_bruto)
    potencia_sistema_kwp = (qtd_modulos * potencia_final) / 1000

    st.session_state['qtd_modulos_final'] = qtd_modulos

    # Layout de Exibição em Colunas
    col_res1, col_res2 = st.columns(2)

    with col_res1:
        # Card de Consumo (Design Original)
        st.markdown(f"""
            <div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; height: 160px;">
                <p style="color: white; margin: 0;">Consumo Base: <b>{consumo_base_calculo:.1f} kWh</b></p>
                <p style="color: #ffa500; margin: 0; font-size: 0.9em;">+ Adicional ({detalhe_sobra}): <b>{valor_sobra:.1f} kWh</b></p>
                <hr style="margin: 10px 0; border: 0.5px solid rgba(255,255,255,0.2);">
                <p style="color: white; font-size: 1.1em; margin: 0;">Consumo Final: <b>{consumo_total_projeto:.1f} kWh</b></p>
            </div>
        """, unsafe_allow_html=True)

    with col_res2:
        # Card de Módulos (Design Igualado ao Consumo)
        st.markdown(f"""
            <div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; height: 160px;">
                <p style="color: white; margin: 0;">Quantidade de Módulos Necessária:</p>
                <p style="color: #ffa500; margin: 0; font-size: 1.6em; font-weight: bold;">{qtd_modulos}</p>
                <hr style="margin: 10px 0; border: 0.5px solid rgba(255,255,255,0.2);">
                <p style="color: white; font-size: 1.1em; margin: 0;">Potência Total do Sistema: <b>{potencia_sistema_kwp:.2f} kWp</b></p>
            </div>
        """, unsafe_allow_html=True)
else:
    # Se a potência ainda não estiver definida, exibe apenas o card de consumo em largura total
    st.markdown(f"""
        <div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; margin-bottom: 20px;">
            <p style="color: white; margin: 0;">Consumo Base: <b>{consumo_base_calculo:.1f} kWh</b></p>
            <p style="color: #ffa500; margin: 0; font-size: 0.9em;">+ Adicional ({detalhe_sobra}): <b>{valor_sobra:.1f} kWh</b></p>
            <hr style="margin: 10px 0; border: 0.5px solid rgba(255,255,255,0.2);">
            <p style="color: white; font-size: 1.2em; margin: 0;">Consumo Final: <b>{consumo_total_projeto:.1f} kWh</b></p>
        </div>
    """, unsafe_allow_html=True)

# --- SEÇÃO 10: GRÁFICO DE CONSUMO vs GERAÇÃO ---
st.markdown('<p class="section-header">GRÁFICO DE CONSUMO vs GERAÇÃO (12 MESES)</p>', unsafe_allow_html=True)

import altair as alt
import pandas as pd

# 1. Definição da produtividade mensal por cada Watt (W) de módulo
produtividade_mensal = {
    "JAN": 0.1350887, "FEV": 0.1110645, "MAR": 0.1031129, "ABR": 0.0817097,
    "MAI": 0.0722258, "JUN": 0.0558870, "JUL": 0.0639952, "AGO": 0.0775323,
    "SET": 0.0876129, "OUT": 0.1100323, "NOV": 0.1272935, "DEZ": 0.1454113
}

# 2. Recuperação de dados técnicos da Seção 9 e cálculos de potência
qtd_modulos = st.session_state.get('qtd_modulos_final', 0)
potencia_mod = st.session_state.get('potencia_modulo_final', 0)
potencia_total_w = float(qtd_modulos) * float(potencia_mod)

ordem_meses = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
dados_combinados = []

# 3. Lógica de recuperação de Consumo (Tratamento de PDF e Histórico Manual)
metodo = st.session_state.get('metodo_consumo_key')
formato_manual = st.session_state.get('formato_consumo_key')

if metodo == "Leitura de PDF" or (metodo == "Manual" and formato_manual == "Histórico 12 Meses"):
    historico = st.session_state.get('historico_12_meses_key', {})
    valores_existentes = [float(v) for v in historico.values() if v and float(v) > 0]
    media_cons = sum(valores_existentes) / len(valores_existentes) if valores_existentes else 0.0
else:
    media_cons = float(st.session_state.get('consumo_final_key', 0.0))
    historico = {m: media_cons for m in ordem_meses}

# 4. Construção da lista de dados para o gráfico
for mes in ordem_meses:
    # Consumo
    val_cons = float(historico.get(mes, 0.0))
    if val_cons == 0: val_cons = media_cons
    dados_combinados.append({"Mês": mes, "Valor": round(val_cons, 1), "Tipo": "Consumo"})

    # Geração
    val_geracao = potencia_total_w * produtividade_mensal[mes]
    dados_combined_item = {"Mês": mes, "Valor": round(val_geracao, 1), "Tipo": "Geração"}
    dados_combinados.append(dados_combined_item)

df_grafico = pd.DataFrame(dados_combinados)

# 5. Criação da Base do Gráfico
# Alteramos as cores dos eixos para cinza escuro/preto para garantir visibilidade no fundo branco
base = alt.Chart(df_grafico).encode(
    x=alt.X('Mês:N', sort=ordem_meses, title=None, axis=alt.Axis(labelAngle=0, labelColor='#333333')),
    y=alt.Y('Valor:Q', title=None, axis=alt.Axis(grid=True, gridColor='rgba(0,0,0,0.1)', labelColor='#333333')),
    xOffset='Tipo:N',
    color=alt.Color('Tipo:N',
                    scale=alt.Scale(domain=['Consumo', 'Geração'], range=['#000080', '#ffa500']),
                    legend=alt.Legend(
                        orient='bottom',
                        title=None,
                        labelColor='#333333',  # Cor da legenda alterada para cinza escuro
                        symbolType='square',
                        labelFontSize=12
                    )
                    ),
    tooltip=['Mês', 'Tipo', 'Valor']
).properties(height=400)

# 6. Camada de Barras
bars = base.mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)

# 7. Camada de Texto (Valores Exatos)
# Cor do texto alterada para preto/cinza para aparecer no fundo branco
text = base.mark_text(
    align='center',
    baseline='bottom',
    dy=-5,
    color='#333333',
    fontSize=10,
    fontWeight='bold'
).encode(
    text=alt.Text('Valor:Q', format='.0f')
)

# 8. Unificação e Configurações de Visualização
chart_final = (bars + text).configure_view(
    stroke=None
).configure_axis(
    domain=False
)

# 9. Exibição final
if potencia_total_w > 0:
    st.altair_chart(chart_final, use_container_width=True)
else:
    st.warning("⚠️ Aguardando definição do sistema para gerar o gráfico.")

# --- SEÇÃO 11: DIMENSIONAMENTO AUTOMÁTICO DE INVERSOR ---

# A lógica só executa se o Modo Manual NÃO estiver ativo
# Verificamos ambas as chaves possíveis para garantir a segurança
modo_manual_ativo = st.session_state.get('orc_man_key') or st.session_state.get('orc_man_disabled')

if not modo_manual_ativo:
    # 1. Recuperar dados base
    qtd_modulos_base = st.session_state.get('qtd_modulos_final', 0)
    potencia_mod_w = st.session_state.get('potencia_modulo_final', 0)

    # 2. Aplicar Sobra de Inversor (se houver)
    qtd_para_inversor = qtd_modulos_base

    if st.session_state.get('sobra_inv_key'):
        porcentagem_sobra = st.session_state.get('pc_sobra_inv_key', 0.0)
        if porcentagem_sobra > 0:
            qtd_para_inversor = math.ceil(qtd_modulos_base * (1 + (porcentagem_sobra / 100)))

    # 3. Potência total calculada para o Inversor (kWp)
    potencia_considerada_kwp = (qtd_para_inversor * potencia_mod_w) / 1000

    # 4. Lógica de busca do Inversor com Overload de 50%
    potencia_minima_inversor = potencia_considerada_kwp / 1.5

    try:
        marca_escolhida = st.session_state.get('marca_key')
        df_inversores = pd.read_excel(r"precos_lumo.xlsx", sheet_name="Inversores")

        filtro_inversores = df_inversores[
            (df_inversores.iloc[:, 0] == marca_escolhida) &
            (df_inversores.iloc[:, 1] >= potencia_minima_inversor)
            ].sort_values(by=df_inversores.columns[1])

        if not filtro_inversores.empty:
            inversor_ideal = filtro_inversores.iloc[0, 1]

            # Exibição apenas do Inversor Sugerido
            st.markdown(f"""
                <div style="background-color: rgba(255, 255, 255, 0.1); padding: 20px; border-radius: 10px; border-left: 5px solid #ffa500; text-align: center; margin-top: 10px;">
                    <p style="color: white; margin: 0; font-size: 1.1em;">Inversor Sugerido ({marca_escolhida}):</p>
                    <p style="color: #ffa500; font-size: 2em; font-weight: bold; margin: 0;">{inversor_ideal} kW</p>
                </div>
            """, unsafe_allow_html=True)

            st.session_state['inversor_selecionado_final'] = inversor_ideal
        else:
            st.warning(f"⚠️ Nenhum inversor da marca {marca_escolhida} atende a potência necessária.")

    except Exception as e:
        st.error(f"Erro ao dimensionar inversor: {e}")

# --- SEÇÃO 12: DIMENSIONAMENTO DE ESTRUTURAS ---
st.markdown('<p class="section-header">ESTRUTURAS</p>', unsafe_allow_html=True)

tipo_telhado = st.session_state.get('tipo_telhado_key')
X = st.session_state.get('qtd_modulos_final', 0)

if tipo_telhado in ["Laje", "Solo", "Kalheta"]:
    st.session_state['custo_estrutura_final'] = 0.0
    # Limpando registros anteriores se mudar o telhado
    st.session_state['pdf_q_perfil'] = 0
    st.session_state['pdf_q_t_final'] = 0
    st.session_state['pdf_q_t_inter'] = 0
    st.session_state['pdf_q_p_estru'] = 0
    st.session_state['pdf_q_sup_cer'] = 0
else:
    try:
        df_estruturas = pd.read_excel(r"precos_lumo.xlsx", sheet_name="Estruturas")
        precos = dict(zip(df_estruturas.iloc[:, 0], df_estruturas.iloc[:, 1]))

        est_metalica_check = st.checkbox("Estrutura metálica", key='est_metalica_key')
        valor_metalica_adicional = 0.0
        if est_metalica_check:
            valor_metalica_adicional = st.number_input("Valor da Estrutura Metálica (R$)", min_value=0.0, step=100.0,
                                                       key='valor_metalica_input')

        if X > 0:
            Y = X / 2
            sug_perfil = (Y + 1) if X % 2 == 0 else math.ceil(Y)
            sug_t_final = (X * 2) if X % 2 == 0 else (X * 2) + 2
            sug_t_inter = max(0, (X * 2) - 2)
            sug_sup_cer = ((X * 2) + 2) if tipo_telhado == "Telha" else 0
        else:
            sug_perfil = sug_t_final = sug_t_inter = sug_sup_cer = 0

        st.markdown(f'<p style="color: #ffa500; font-weight: bold;">Ajuste de Quantidades ({tipo_telhado})</p>',
                    unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            q_perfil = st.number_input("Perfil", min_value=0, value=int(sug_perfil), step=1)
            q_t_final = st.number_input("T Final", min_value=0, value=int(sug_t_final), step=1)
        with col2:
            q_t_inter = st.number_input("T Interm.", min_value=0, value=int(sug_t_inter), step=1)
            q_p_estru = st.number_input("P Estrutural", min_value=0, value=0, step=1)
        with col3:
            if tipo_telhado == "Telha":
                q_sup_cer = st.number_input("Sup. Cerâmico", min_value=0, value=int(sug_sup_cer), step=1)
            else:
                q_sup_cer = 0

        # --- AQUI ESTÁ O SEGREDO: SALVAR PARA O PDF ---
        st.session_state['pdf_q_perfil'] = q_perfil
        st.session_state['pdf_q_t_final'] = q_t_final
        st.session_state['pdf_q_t_inter'] = q_t_inter
        st.session_state['pdf_q_p_estru'] = q_p_estru
        st.session_state['pdf_q_sup_cer'] = q_sup_cer

        custo_perfil = q_perfil * precos.get('Perfil', 0)
        custo_t_final = q_t_final * precos.get('T Final', 0)
        custo_t_inter = q_t_inter * precos.get('T Intermediário', 0)
        custo_sup_cer = q_sup_cer * precos.get('Sup Cerâmico', 0)
        custo_p_estru = q_p_estru * precos.get('P Estrutural', 0)

        total_estrutura = custo_perfil + custo_t_final + custo_t_inter + custo_sup_cer + custo_p_estru + valor_metalica_adicional
        st.session_state['custo_estrutura_final'] = total_estrutura

        st.markdown(
            f'<p style="color: #ffa500; font-weight: bold;">Valor total de Estruturas: R$ {total_estrutura:,.2f}</p>',
            unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro ao processar estruturas: {e}")

# --- SEÇÃO 13: CUSTOS DE INSTALAÇÃO, MATERIAL, PROJETO E CESTA ---
import pandas as pd
import os
import re

# 1. Resgate de Variáveis de Controle
qtd_modulos_ref = st.session_state.get('qtd_modulos_com_sobra_final',
                                       st.session_state.get('qtd_modulos_final', 0))

tipo_usina_selecionado = st.session_state.get('modo_usina_key', "")
e_microinversor = (tipo_usina_selecionado == "Microinversor")

# 2. Checkboxes de Controle (Organizados em 4 Colunas)
st.markdown('<p style="color: white; font-size: 1.1em; margin-bottom: 10px;">Configurações Manuais:</p>',
            unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    inst_manual_ativo = st.checkbox("Instalação Manual", key="check_inst_manual")
with c2:
    mat_manual_ativo = st.checkbox("Mat. ele Manual", key="check_mat_manual")
with c3:
    proj_manual_ativo = st.checkbox("Projeto Manual", key="check_proj_manual")
with c4:
    sem_cesta_ativo = st.checkbox("Sem cesta", key="check_sem_cesta")

# Inicialização de valores
custo_instalacao = 0.0
custo_material = 0.0
custo_projeto = 0.0
custo_cesta = 0.0

try:
    caminho_excel = r"precos_lumo.xlsx"

    if os.path.exists(caminho_excel):
        # --- LÓGICA INSTALAÇÃO ---
        if inst_manual_ativo:
            custo_instalacao = st.number_input("Valor da Instalação (R$)", min_value=0.0, step=100.0,
                                               key="val_inst_input")
        else:
            df_fixo = pd.read_excel(caminho_excel, sheet_name='Custo Fixo')
            for _, row in df_fixo.iterrows():
                nums = re.findall(r'\d+', str(row.iloc[0]))
                if len(nums) == 2 and int(nums[0]) <= qtd_modulos_ref <= int(nums[1]):
                    custo_instalacao = float(row.iloc[1]);
                    break
                elif len(nums) == 1 and ("+" in str(row.iloc[0]) or "acima" in str(row.iloc[0]).lower()):
                    if qtd_modulos_ref >= int(nums[0]):
                        custo_instalacao = float(row.iloc[1]);
                        break
            if e_microinversor: custo_instalacao *= 1.25

        # --- LÓGICA MATERIAL ELÉTRICO ---
        if mat_manual_ativo:
            custo_material = st.number_input("Valor do Material Elétrico (R$)", min_value=0.0, step=100.0,
                                             key="val_mat_input")
        else:
            df_mat = pd.read_excel(caminho_excel, sheet_name='material eletrico')
            for _, row in df_mat.iterrows():
                nums = re.findall(r'\d+', str(row.iloc[0]))
                if len(nums) == 2 and int(nums[0]) <= qtd_modulos_ref <= int(nums[1]):
                    custo_material = float(row.iloc[1]);
                    break
                elif len(nums) == 1 and ("+" in str(row.iloc[0]) or "acima" in str(row.iloc[0]).lower()):
                    if qtd_modulos_ref >= int(nums[0]):
                        custo_material = float(row.iloc[1]);
                        break

        # --- LÓGICA PROJETO ---
        if proj_manual_ativo:
            custo_projeto = st.number_input("Valor do Projeto (R$)", min_value=0.0, step=50.0, key="val_proj_input")
        else:
            df_proj_cesta = pd.read_excel(caminho_excel, sheet_name='projeto e cesta')
            row_projeto = df_proj_cesta[df_proj_cesta.iloc[:, 0].astype(str).str.strip().str.lower() == 'projeto']
            if not row_projeto.empty:
                custo_projeto = float(row_projeto.iloc[0, 1])

        # --- LÓGICA CESTA ---
        if sem_cesta_ativo:
            custo_cesta = 0.0
        else:
            df_proj_cesta = pd.read_excel(caminho_excel, sheet_name='projeto e cesta')
            row_cesta = df_proj_cesta[df_proj_cesta.iloc[:, 0].astype(str).str.strip().str.lower() == 'cesta']
            if not row_cesta.empty:
                custo_cesta = float(row_cesta.iloc[0, 1])

    # Salva no session_state para uso futuro
    st.session_state['custo_instalacao_final'] = custo_instalacao
    st.session_state['custo_material_final'] = custo_material
    st.session_state['custo_projeto_final'] = custo_projeto
    st.session_state['custo_cesta_final'] = custo_cesta

    # --- 3. EXIBIÇÃO COM DESIGN DE CARDS (4 COLUNAS) ---
    st.write("")
    col1, col2, col3, col4 = st.columns(4)

    # Card 1: Instalação
    with col1:
        leg_inst = "Manual" if inst_manual_ativo else ("Automática (+25% Micro)" if e_microinversor else "Automática")
        st.markdown(f"""
            <div style="background-color: rgba(255, 255, 255, 0.1); padding: 12px; border-radius: 10px; border-left: 5px solid #ffa500; height: 130px;">
                <p style="color: white; margin: 0; font-size: 0.9em;">Custo de <b>Instalação</b></p>
                <p style="color: #ffa500; margin: 0; font-size: 0.75em;">{leg_inst}</p>
                <hr style="margin: 8px 0; border: 0.5px solid rgba(255,255,255,0.2);">
                <p style="color: white; font-size: 1.2em; font-weight: bold; margin: 0;">R$ {custo_instalacao:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)

    # Card 2: Material Elétrico
    with col2:
        leg_mat = "Manual" if mat_manual_ativo else "Automático"
        st.markdown(f"""
            <div style="background-color: rgba(255, 255, 255, 0.1); padding: 12px; border-radius: 10px; border-left: 5px solid #ffa500; height: 130px;">
                <p style="color: white; margin: 0; font-size: 0.9em;">Material <b>Elétrico</b></p>
                <p style="color: #ffa500; margin: 0; font-size: 0.75em;">{leg_mat}</p>
                <hr style="margin: 8px 0; border: 0.5px solid rgba(255,255,255,0.2);">
                <p style="color: white; font-size: 1.2em; font-weight: bold; margin: 0;">R$ {custo_material:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)

    # Card 3: Projeto
    with col3:
        leg_proj = "Manual" if proj_manual_ativo else "Automático"
        st.markdown(f"""
            <div style="background-color: rgba(255, 255, 255, 0.1); padding: 12px; border-radius: 10px; border-left: 5px solid #ffa500; height: 130px;">
                <p style="color: white; margin: 0; font-size: 0.9em;">Custo de <b>Projeto</b></p>
                <p style="color: #ffa500; margin: 0; font-size: 0.75em;">{leg_proj}</p>
                <hr style="margin: 8px 0; border: 0.5px solid rgba(255,255,255,0.2);">
                <p style="color: white; font-size: 1.2em; font-weight: bold; margin: 0;">R$ {custo_projeto:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)

    # Card 4: Cesta
    with col4:
        leg_cesta = "Removido" if sem_cesta_ativo else "Automático"
        st.markdown(f"""
            <div style="background-color: rgba(255, 255, 255, 0.1); padding: 12px; border-radius: 10px; border-left: 5px solid #ffa500; height: 130px;">
                <p style="color: white; margin: 0; font-size: 0.9em;">Custo de <b>Cesta</b></p>
                <p style="color: #ffa500; margin: 0; font-size: 0.75em;">{leg_cesta}</p>
                <hr style="margin: 8px 0; border: 0.5px solid rgba(255,255,255,0.2);">
                <p style="color: white; font-size: 1.2em; font-weight: bold; margin: 0;">R$ {custo_cesta:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro na Seção 13: {e}")

# --- SEÇÃO 14: VALOR KIT FOTOVOLTAICO ---
import pandas as pd
import os
import math

# 1. Resgate de variáveis de controle e dados técnicos
modo_manual_ativo = st.session_state.get('orc_man_key') or st.session_state.get('orc_man_disabled')
modulo_manual_ativo = st.session_state.get('def_modulo_man_key', False)
marca_sel = st.session_state.get('marca_key')
qtd_mods = st.session_state.get('qtd_modulos_final', 0)
potencia_mod_w = st.session_state.get('potencia_modulo_final', 0)

qtd_inversores = st.session_state.get('qtd_inversores_manual_key', 1)
if qtd_inversores is None or qtd_inversores < 1:
    qtd_inversores = 1

if modo_manual_ativo:
    potencia_inv_sel = st.session_state.get('potencia_key')
else:
    potencia_inv_sel = st.session_state.get('inversor_selecionado_final')

# 2. Inicialização de variáveis
valor_inversor_unit = 0.0
valor_modulo_unit = 0.0
valor_kit_final = 0.0
overload_decimal = 1.50

try:
    caminho_excel = r"precos_lumo.xlsx"

    if os.path.exists(caminho_excel):
        if marca_sel and potencia_inv_sel:
            df_inv = pd.read_excel(caminho_excel, sheet_name="Inversores")
            filtro_inv = df_inv[(df_inv.iloc[:, 0] == marca_sel) & (df_inv.iloc[:, 1] == potencia_inv_sel)]

            if not filtro_inv.empty:
                valor_inversor_unit = float(filtro_inv.iloc[0, 2])
                val_overload = filtro_inv.iloc[0, 3]
                if val_overload > 5:
                    overload_decimal = 1 + (float(val_overload) / 100)
                else:
                    overload_decimal = float(val_overload)

        if marca_sel:
            df_mod = pd.read_excel(caminho_excel, sheet_name="Módulo")
            filtro_mod = df_mod[df_mod.iloc[:, 0] == marca_sel]
            if not filtro_mod.empty:
                valor_modulo_unit = float(filtro_mod.iloc[0, 2])

    # 3. Lógica de Cálculo
    total_inversores = valor_inversor_unit * qtd_inversores
    total_placas = valor_modulo_unit * qtd_mods
    total_automatico = total_inversores + total_placas

    # --- CÁLCULO TÉCNICO DA SOBRA (SALVO NO STATE) ---
    sobra_modulos = 0
    if potencia_inv_sel and potencia_mod_w > 0:
        capacidade_max_kwp = (float(potencia_inv_sel) * overload_decimal) * qtd_inversores
        potencia_atual_kwp = (qtd_mods * potencia_mod_w) / 1000
        sobra_kwp = capacidade_max_kwp - potencia_atual_kwp
        if sobra_kwp > 0:
            sobra_modulos = math.floor((sobra_kwp * 1000) / potencia_mod_w)

    st.session_state['sobra_modulos_final'] = sobra_modulos

    # 4. Lógica de Exibição / Entrada Manual
    if modo_manual_ativo and modulo_manual_ativo:
        valor_kit_final = st.number_input("Valor do Kit Fotovoltaico (R$)", min_value=0.0, step=500.0,
                                          key="valor_kit_obrigatorio")
    else:
        st.write("")
        check_kit_manual = st.checkbox("Valor do Kit manual", key="check_kit_manual_key")
        if check_kit_manual:
            valor_kit_final = st.number_input("Valor do Kit Fotovoltaico (R$)", min_value=0.0, step=500.0,
                                              key="valor_kit_manual_input")
        else:
            valor_kit_final = total_automatico

    st.session_state['valor_kit_projeto_final'] = valor_kit_final

    # 6. Cards Visuais
    if valor_kit_final > 0:
        col_det1, col_det2 = st.columns(2)
        if not (modo_manual_ativo and modulo_manual_ativo) and not st.session_state.get('check_kit_manual_key'):
            with col_det1:
                texto_qtd_inv = f"({qtd_inversores} un)" if qtd_inversores > 1 else ""
                st.markdown(
                    f'<div style="background-color: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 10px; border-left: 3px solid #ffa500;"><p style="color: white; margin: 0; font-size: 0.8em;">Inversor {texto_qtd_inv}:</p><p style="color: white; font-weight: bold; margin: 0;">R$ {total_inversores:,.2f}</p></div>',
                    unsafe_allow_html=True)
            with col_det2:
                st.markdown(
                    f'<div style="background-color: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 10px; border-left: 3px solid #ffa500;"><p style="color: white; margin: 0; font-size: 0.8em;">Placas ({qtd_mods} un):</p><p style="color: white; font-weight: bold; margin: 0;">R$ {total_placas:,.2f}</p></div>',
                    unsafe_allow_html=True)

        st.markdown(
            f'<div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #00ff00; margin-top: 10px;"><p style="color: white; margin: 0; font-size: 1em;">Valor total do <b>Kit Fotovoltaico</b></p><hr style="margin: 10px 0; border: 0.5px solid rgba(255,255,255,0.2);"><p style="color: white; font-size: 1.8em; font-weight: bold; margin: 0;">R$ {valor_kit_final:,.2f}</p></div>',
            unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro ao processar os valores do kit: {e}")

# --- SEÇÃO 15: LUCRO E REPRESENTANTE ---
import pandas as pd
import os
import re

# 1. Resgate de Variáveis de Controle
qtd_modulos_ref = st.session_state.get('qtd_modulos_com_sobra_final',
                                       st.session_state.get('qtd_modulos_final', 0))

# Estado do representante (Seção 6)
representante_ativo = st.session_state.get('representante_v', False)

# 2. Checkbox para Lucro Manual
st.write("")
lucro_manual_ativo = st.checkbox("Inserir lucro manual", key="check_lucro_manual")

lucro_valor = 0.0
representante_valor = 0.0

try:
    caminho_excel = r"precos_lumo.xlsx"

    # 3. Definição do Valor do Lucro
    if lucro_manual_ativo:
        # Entrada manual
        lucro_valor = st.number_input("Digite a margem de lucro desejada (R$)", min_value=0.0, step=100.0,
                                      key="input_lucro_manual")
    else:
        # Busca Automática no Excel
        if os.path.exists(caminho_excel):
            df_lucro = pd.read_excel(caminho_excel, sheet_name='lucro')

            for _, row in df_lucro.iterrows():
                faixa_texto = str(row.iloc[0])
                numeros = re.findall(r'\d+', faixa_texto)

                if len(numeros) == 2:
                    inicio, fim = int(numeros[0]), int(numeros[1])
                    if inicio <= qtd_modulos_ref <= fim:
                        lucro_valor = float(row.iloc[1])
                        break
                elif len(numeros) == 1 and ("+" in faixa_texto or "acima" in faixa_texto.lower()):
                    if qtd_modulos_ref >= int(numeros[0]):
                        lucro_valor = float(row.iloc[1])
                        break

    # 4. Lógica do Representante (Espelha o lucro atual, seja manual ou automático)
    if representante_ativo:
        representante_valor = lucro_valor
    else:
        representante_valor = 0.0

    # 5. Salva no session_state para o fechamento final
    st.session_state['valor_lucro_final'] = lucro_valor
    st.session_state['valor_representante_final'] = representante_valor

    # 6. Exibição Visual em Cards
    st.write("")
    col_lucro, col_rep = st.columns(2)

    with col_lucro:
        origem_lucro = "Manual" if lucro_manual_ativo else "Automático (Planilha)"
        st.markdown(f"""
            <div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; height: 130px;">
                <p style="color: white; margin: 0; font-size: 1em;">Margem de <b>Lucro</b></p>
                <p style="color: #ffa500; margin: 0; font-size: 0.8em;">Origem: {origem_lucro}</p>
                <hr style="margin: 10px 0; border: 0.5px solid rgba(255,255,255,0.2);">
                <p style="color: white; font-size: 1.5em; font-weight: bold; margin: 0;">R$ {lucro_valor:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)

    with col_rep:
        status_rep = "Ativo (Espelhando Lucro)" if representante_ativo else "Desativado"
        st.markdown(f"""
            <div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; height: 130px;">
                <p style="color: white; margin: 0; font-size: 1em;">Comissão <b>Representante</b></p>
                <p style="color: #ffa500; margin: 0; font-size: 0.8em;">Status: {status_rep}</p>
                <hr style="margin: 10px 0; border: 0.5px solid rgba(255,255,255,0.2);">
                <p style="color: white; font-size: 1.5em; font-weight: bold; margin: 0;">R$ {representante_valor:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro na Seção 15: {e}")

# --- SEÇÃO 16: IMPOSTO E INDICAÇÃO ---
import pandas as pd
import os
import streamlit as st

st.markdown('<p class="section-header">IMPOSTO E INDICAÇÃO</p>', unsafe_allow_html=True)

# 1. Checkbox para Zerar Imposto
col_ctrl1, col_ctrl2 = st.columns(2)
with col_ctrl1:
    zerar_imposto = st.checkbox("Zerar imposto", key='zerar_imposto_key')

# 2. Resgate de Variáveis de Controle e Custos
indicador_ativo = st.session_state.get('indicador_key', False)
tipo_indicador = st.session_state.get('tipo_indicador_key', "Porcentagem")

# Conversão segura de valores numéricos
pc_ind_digitada = float(
    st.session_state.get('pc_indicador_key', 0.0)) if indicador_ativo and tipo_indicador == "Porcentagem" else 0.0
val_ind_digitado = float(
    st.session_state.get('valor_indicador_key', 0.0)) if indicador_ativo and tipo_indicador == "Valor" else 0.0

# Resgate de todos os custos para a somatória base
c_inst = float(st.session_state.get('custo_instalacao_final', 0.0))
c_mat = float(st.session_state.get('custo_material_final', 0.0))
c_proj = float(st.session_state.get('custo_projeto_final', 0.0))
c_cest = float(st.session_state.get('custo_cesta_final', 0.0))
c_lucr = float(st.session_state.get('valor_lucro_final', 0.0))
c_repr = float(st.session_state.get('valor_representante_final', 0.0))
c_estru = float(st.session_state.get('custo_estrutura_final', 0.0))
v_kit = float(st.session_state.get('valor_kit_projeto_final', 0.0))

# Somatória Base (Serviços + Lucro + Representante + Estrutura + Indicação se valor fixo)
somatoria_base = c_inst + c_mat + c_proj + c_cest + c_lucr + c_repr + c_estru + val_ind_digitado

imposto_pc = 0.0

try:
    # Caminho configurado para teste local no PyCharm
    caminho_excel = r"precos_lumo.xlsx"

    if os.path.exists(caminho_excel):
        df_kwh = pd.read_excel(caminho_excel, sheet_name='kwh')
        # Busca a linha que contém a palavra 'imposto' na primeira coluna
        row_imposto = df_kwh[df_kwh.iloc[:, 0].astype(str).str.strip().str.lower().str.contains('imposto')]
        if not row_imposto.empty:
            imposto_pc = float(row_imposto.iloc[0, 1])

    # --- LÓGICA DE APLICAÇÃO DO CHECKBOX "ZERAR IMPOSTO" ---
    if zerar_imposto:
        imposto_pc = 0.0

    # --- LÓGICA DE CÁLCULO RECURSIVA (MARK-UP) ---
    taxa_imp = imposto_pc / 100
    taxa_ind = pc_ind_digitada / 100

    # Divisor comum para equilíbrio matemático das incidências cruzadas
    divisor_comum = (1 - taxa_imp - taxa_ind)

    if divisor_comum <= 0:
        st.error("Erro: As taxas de Imposto e Indicação somadas são iguais ou superiores a 100%.")
        val_final_imposto = 0.0
        val_final_indicacao = 0.0
    else:
        # Cálculo do valor final do Imposto estabilizado
        val_final_imposto = ((somatoria_base * taxa_imp) + (v_kit * taxa_ind * taxa_imp)) / divisor_comum

        # Cálculo do valor final da Indicação estabilizado
        if indicador_ativo and tipo_indicador == "Porcentagem":
            val_final_indicacao = ((somatoria_base * taxa_ind) + (v_kit * taxa_ind) + (
                        val_final_imposto * taxa_ind)) / (1 - taxa_ind)
        else:
            val_final_indicacao = val_ind_digitado

    # Salvando no session_state para uso no fechamento final
    st.session_state['imposto_valor_calculado'] = val_final_imposto
    st.session_state['indicacao_valor_calculado'] = val_final_indicacao
    st.session_state['imposto_pc_final'] = imposto_pc

    # --- EXIBIÇÃO DOS CARDS ---
    st.write("")
    col_d1, col_d2 = st.columns(2)

    with col_d1:
        cor_imposto = "#ffffff" if not zerar_imposto else "#888888"
        st.markdown(f"""
            <div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; height: 130px;">
                <p style="color: white; margin: 0; font-size: 1em;">Valor do <b>Imposto</b> ({imposto_pc}%)</p>
                <p style="color: #ffa500; margin: 0; font-size: 0.8em;">Incidência: Faturamento Total</p>
                <hr style="margin: 10px 0; border: 0.5px solid rgba(255,255,255,0.2);">
                <p style="color: {cor_imposto}; font-size: 1.5em; font-weight: bold; margin: 0;">R$ {val_final_imposto:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)

    with col_d2:
        leg_ind = f"{pc_ind_digitada}%" if tipo_indicador == "Porcentagem" else "Valor Fixo"
        st.markdown(f"""
            <div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; height: 130px;">
                <p style="color: white; margin: 0; font-size: 1em;">Valor da <b>Indicação</b></p>
                <p style="color: #ffa500; margin: 0; font-size: 0.8em;">Base: {leg_ind}</p>
                <hr style="margin: 10px 0; border: 0.5px solid rgba(255,255,255,0.2);">
                <p style="color: white; font-size: 1.5em; font-weight: bold; margin: 0;">R$ {val_final_indicacao:,.2f}</p>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro na Seção 16: {e}")

# --- SEÇÃO 17: FECHAMENTO DO ORÇAMENTO ---
import math

st.markdown('<p class="section-header">VALOR FINAL DO ORÇAMENTO</p>', unsafe_allow_html=True)

# 1. Resgate de todos os valores finais
v_kit   = st.session_state.get('valor_kit_projeto_final', 0.0)
c_inst  = st.session_state.get('custo_instalacao_final', 0.0)
c_mat   = st.session_state.get('custo_material_final', 0.0)
c_proj  = st.session_state.get('custo_projeto_final', 0.0)
c_cest  = st.session_state.get('custo_cesta_final', 0.0)
c_lucr  = st.session_state.get('valor_lucro_final', 0.0)
c_repr  = st.session_state.get('valor_representante_final', 0.0)
c_estru = st.session_state.get('custo_estrutura_final', 0.0)
v_imp   = st.session_state.get('imposto_valor_calculado', 0.0)
v_ind   = st.session_state.get('indicacao_valor_calculado', 0.0)

# 2. Cálculo do Valor Bruto (Sem arredondamento)
valor_bruto = (
    v_kit + c_inst + c_mat + c_proj + c_cest +
    c_lucr + c_repr + c_estru + v_imp + v_ind
)

# 3. Lógica de Arredondamento para cima (Centenas)
# Ex: 15.058 -> 15.100
valor_arredondado = math.ceil(valor_bruto / 100) * 100

# Trata a exceção específica: se o final for .900 e o bruto era um pouco menor (como seu exemplo de 15.990)
# Se o valor arredondado termina em X.000 e o bruto era entre X.950 e X.990
resto_milhar = valor_bruto % 1000
if 950 <= resto_milhar < 990:
    valor_arredondado = (math.floor(valor_bruto / 1000) * 1000) + 990

# 4. Exibição com destaque visual
st.markdown(f"""
    <div style="background-color: #ffa500; padding: 30px; border-radius: 15px; text-align: center; margin-top: 20px;">
        <p style="color: #1e1e1e; margin: 0; font-size: 1.2em; font-weight: bold; text-transform: uppercase;">Valor Total do Investimento</p>
        <h1 style="color: #1e1e1e; margin: 0; font-size: 3.5em; font-weight: 900;">R$ {valor_arredondado:,.2f}</h1>
        <p style="color: #1e1e1e; margin: 0; font-size: 0.9em; opacity: 0.8;">Sistema completo com instalação e homologação</p>
    </div>
""", unsafe_allow_html=True)

# Guardar valor total arredondado
st.session_state['valor_total_final_projeto'] = valor_arredondado

# --- SEÇÃO 18: RETORNO FINANCEIRO (ATUALIZADA COM LÓGICA RURAL) ---
import pandas as pd
import os

st.markdown('<p class="section-header">RETORNO FINANCEIRO</p>', unsafe_allow_html=True)

# 1. Checkbox de Controle de Exibição
exibir_detalhe_fatura = st.checkbox("Detalhamento de Fatura", key="check_detalhe_fatura")

# 2. Resgate de dados de Geração, Consumo, Valor Total e Perfil Rural
produtividade_mensal = {
    "JAN": 0.1350887, "FEV": 0.1110645, "MAR": 0.1031129, "ABR": 0.0817097,
    "MAI": 0.0722258, "JUN": 0.0558870, "JUL": 0.0639952, "AGO": 0.0775323,
    "SET": 0.0876129, "OUT": 0.1100323, "NOV": 0.1272935, "DEZ": 0.1454113
}
qtd_modulos = st.session_state.get('qtd_modulos_final', 0)
potencia_mod = st.session_state.get('potencia_modulo_final', 0)
potencia_total_w = float(qtd_modulos) * float(potencia_mod)
valor_total_investimento = st.session_state.get('valor_total_final_projeto', 0.0)
is_rural = st.session_state.get('cliente_rural_key', False)

# Geração Média Mensal
media_geracao_kwh = (potencia_total_w * sum(produtividade_mensal.values())) / 12
media_geracao_grafico = round(media_geracao_kwh, 1)

# Consumo Médio Mensal (Lógica Seção 10)
metodo = st.session_state.get('metodo_consumo_key')
formato_manual = st.session_state.get('formato_consumo_key')
if metodo == "Leitura de PDF" or (metodo == "Manual" and formato_manual == "Histórico 12 Meses"):
    historico = st.session_state.get('historico_12_meses_key', {})
    valores_existentes = [float(v) for v in historico.values() if v and float(v) > 0]
    media_cons = sum(valores_existentes) / len(valores_existentes) if valores_existentes else 0.0
else:
    media_cons = float(st.session_state.get('consumo_final_key', 0.0))
media_cons_grafico = round(media_cons, 1)

tipo_entrada = st.session_state.get('entrada_key', "Monofásica")

try:
    caminho_excel = r"precos_lumo.xlsx"
    if os.path.exists(caminho_excel):
        df_kwh = pd.read_excel(caminho_excel, sheet_name='kwh')


        def get_val(item_nome):
            row = df_kwh[df_kwh.iloc[:, 0].astype(str).str.strip().str.lower() == item_nome.lower()]
            return float(row.iloc[0, 1]) if not row.empty else 0.0


        # --- SELEÇÃO DINÂMICA DE TARIFAS (RURAL vs PADRÃO) ---
        if is_rural:
            t_cheia = get_val('tarifa_rural_cheia')
            t_solar = get_val('tarifa_rural_solar')
            label_perfil = "Rural"
        else:
            t_cheia = get_val('tarifa_cheia')
            t_solar = get_val('tarifa_solar')
            label_perfil = "Padrão"

        consumo_inst = get_val('consumo_instantaneo')

        # Custo de disponibilidade (Z) baseado na entrada
        if tipo_entrada == "Monofásica":
            custo_kwh_disp = get_val('custo_mono')
        elif tipo_entrada == "Bifásica":
            custo_kwh_disp = get_val('custo_bi')
        else:
            custo_kwh_disp = get_val('custo_tri')

        # --- CÁLCULOS FINANCEIROS ---
        # 1. Valor da fatura sem solar
        valor_fatura_sem_solar = media_geracao_kwh * t_cheia

        # 2. Valor médio da fatura estimada (Y + Z)
        # X = Geração * Consumo Instantâneo | Y = X * Tarifa Solar
        valor_Y = (media_geracao_kwh * consumo_inst) * t_solar
        # Z = Custo Disponibilidade * Tarifa Cheia (Rural ou Padrão)
        valor_Z = custo_kwh_disp * t_cheia

        valor_fatura_estimada_solar = valor_Y + valor_Z

        # 3. Economia e Porcentagem
        economia_mensal_nominal = valor_fatura_sem_solar - valor_fatura_estimada_solar
        porcentagem_economia = (
                    economia_mensal_nominal / valor_fatura_sem_solar * 100) if valor_fatura_sem_solar > 0 else 0.0

        # 4. Payback
        if economia_mensal_nominal > 0:
            payback_meses = valor_total_investimento / economia_mensal_nominal
            payback_anos = payback_meses / 12
        else:
            payback_meses = 0
            payback_anos = 0

        # Salva no session_state
        st.session_state['payback_meses'] = payback_meses

        # --- INTERFACE DE USUÁRIO ---
        if exibir_detalhe_fatura:

            # LINHA 1: Geração e Consumo
            col_gra1, col_gra2 = st.columns(2)
            with col_gra1:
                st.markdown(f"""<div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; height: 110px;">
                    <p style="color: white; margin: 0; font-size: 0.9em;">Consumo Médio Mensal</p>
                    <p style="color: white; font-size: 1.4em; font-weight: bold; margin: 0;">{media_cons_grafico} kWh</p>
                </div>""", unsafe_allow_html=True)
            with col_gra2:
                st.markdown(f"""<div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; height: 110px;">
                    <p style="color: white; margin: 0; font-size: 0.9em;">Geração Média Mensal</p>
                    <p style="color: white; font-size: 1.4em; font-weight: bold; margin: 0;">{media_geracao_grafico} kWh</p>
                </div>""", unsafe_allow_html=True)

            # LINHA 2: Faturas
            col_ret1, col_ret2 = st.columns(2)
            with col_ret1:
                st.markdown(f"""<div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; height: 110px; margin-top:10px;">
                    <p style="color: white; margin: 0; font-size: 0.9em;">Valor da fatura sem solar ({label_perfil})</p>
                    <p style="color: white; font-size: 1.4em; font-weight: bold; margin: 0;">R$ {valor_fatura_sem_solar:,.2f}</p>
                </div>""", unsafe_allow_html=True)
            with col_ret2:
                st.markdown(f"""<div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; height: 110px; margin-top:10px;">
                    <p style="color: white; margin: 0; font-size: 0.9em;">Valor médio da fatura estimada</p>
                    <p style="color: white; font-size: 1.4em; font-weight: bold; margin: 0;">R$ {valor_fatura_estimada_solar:,.2f}</p>
                </div>""", unsafe_allow_html=True)

            # LINHA 3: Economia e Payback
            col_eco1, col_pay = st.columns(2)
            with col_eco1:
                st.markdown(f"""<div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; height: 110px; margin-top:10px;">
                    <p style="color: white; margin: 0; font-size: 0.9em;">Economia média mensal estimada</p>
                    <p style="color: white; font-size: 1.4em; font-weight: bold; margin: 0;">R$ {economia_mensal_nominal:,.2f}</p>
                </div>""", unsafe_allow_html=True)
            with col_pay:
                st.markdown(f"""<div style="background-color: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; border-left: 5px solid #ffa500; height: 110px; margin-top:10px;">
                    <p style="color: white; margin: 0; font-size: 0.9em;">Tempo de Retorno (Payback)</p>
                    <p style="color: white; font-size: 1.4em; font-weight: bold; margin: 0;">{int(payback_meses)} meses <span style="font-size: 0.6em; font-weight: normal;">({payback_anos:.1f} anos)</span></p>
                </div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro na Seção 18: {e}")

# --- SEÇÃO 19: GERAÇÃO     DE ORÇAMENTO EM PDF (ESTRUTURA COMPLETA) ---
import io
import os
import re
import math
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from datetime import datetime

try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    st.error("A biblioteca PyPDF2 não foi encontrada. Instale-a com: pip install PyPDF2")

st.markdown('<p class="section-header">GERAR ORÇAMENTO EM PDF</p>', unsafe_allow_html=True)

# 1. CSS do Botão de Download
st.markdown("""
    <style>
    div.stDownloadButton > button {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid #ffa500 !important;
        border-radius: 10px !important;
        padding: 15px 20px !important;
        font-weight: bold !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        height: 60px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div.stDownloadButton > button:hover {
        background-color: #ffa500 !important;
        color: black !important;
    }
    </style>
""", unsafe_allow_html=True)


# --- FUNÇÕES AUXILIARES ---
def buscar_imagem_logo(marca):
    # Removido o caminho C:\ e deixado apenas uma string vazia ou "."
    # para indicar que deve procurar na mesma pasta do código.
    diretorio_logos = ""
    extensoes = ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']

    if not marca:
        return None


# =================================================================
# --- SEÇÃO 19.1: CONTEÚDO DA PÁGINA 3 (EDIÇÃO ATIVA) ---
# =================================================================
def renderizar_pagina_3(can):
    """
    Função dedicada exclusivamente para editar a terceira página.
    """
    caminho_fundo_p3 = r"tres.png"
    largura_a4, altura_a4 = A4

    if os.path.exists(caminho_fundo_p3):
        can.drawImage(caminho_fundo_p3, 0, 0, width=largura_a4, height=altura_a4)

    # --- RESGATE DE DADOS ---
    qtd_mod = float(st.session_state.get('qtd_modulos_final', 0))
    pot_mod_w = float(st.session_state.get('potencia_modulo_final', 0))
    qtd_inv = st.session_state.get('qtd_inversores_manual_key', 1) or 1
    marca_inv = st.session_state.get('marca_key', '')
    pot_inv = st.session_state.get('potencia_key') or st.session_state.get('inversor_selecionado_final', 0)
    sobra_modulos = st.session_state.get('sobra_modulos_final', 0)
    consumo_total_projeto = st.session_state.get('consumo_final_key', 0)

    # Cálculo da Potência Total em kWp e Watts
    pot_total_w = qtd_mod * pot_mod_w
    pot_kwp = pot_total_w / 1000

    # Cálculo da Média de Geração
    prod_mensal_indices = [0.135, 0.111, 0.103, 0.081, 0.072, 0.055, 0.063, 0.077, 0.087, 0.110, 0.127, 0.145]
    media_indice = sum(prod_mensal_indices) / len(prod_mensal_indices)
    geracao_media_estimada = pot_total_w * media_indice

    # --- 1. POTÊNCIA TOTAL (X=467, Y=579) ---
    can.setFont("Helvetica-Bold", 24)
    can.setFillColorRGB(1, 1, 1)
    texto_potencia = f"{pot_kwp:.2f} kWp".replace('.', ',')
    can.drawRightString(467, 579, texto_potencia)

    # --- TEXTOS TÉCNICOS (PRETO, TAMANHO 13) ---
    can.setFont("Helvetica-Bold", 13)
    can.setFillColorRGB(0, 0, 0)

    can.drawCentredString(262, 536, f"Inversor {marca_inv} {pot_inv}k")
    can.drawCentredString(262, 495, f"Módulos de {int(pot_mod_w)}W")
    can.drawCentredString(262, 452, "Inversor com capacidade de ampliar")
    can.drawCentredString(262, 413, "Média atual de consumo")
    can.drawCentredString(262, 373, "Média de geração estimada")
    can.drawCentredString(262, 333, "Valor da fatura atual")
    can.drawCentredString(262, 294, "Economia média mensal estimada")
    can.drawCentredString(262, 256, "Valor médio da fatura estimada")
    can.drawCentredString(262, 214, "Retorno Financeiro")

    # --- VALORES NUMÉRICOS (PRETO, TAMANHO 14) ---
    can.setFont("Helvetica-Bold", 14)

    can.drawCentredString(441, 536, f"{qtd_inv}")
    can.drawCentredString(441, 495, f"{int(qtd_mod)}")
    can.drawCentredString(441, 452, f"{sobra_modulos}")
    can.drawCentredString(441, 413, f"{int(consumo_total_projeto)}kWh")
    can.drawCentredString(441, 373, f"{int(geracao_media_estimada)}kWh")

    # --- FORMATAÇÃO MONETÁRIA BRASILEIRA (R$ 1.234,56) ---
    def f_br(valor):
        # Formata com vírgula no milhar e ponto no decimal, depois inverte
        v = f"{valor:,.2f}"
        return v.replace(",", "X").replace(".", ",").replace("X", ".")

    # 16. valor da fatura atual
    can.drawCentredString(441, 333, f"R$ {f_br(valor_fatura_sem_solar)}")
    # 17. Economia média mensal estimada
    can.drawCentredString(441, 294, f"R$ {f_br(economia_mensal_nominal)}")
    # 18. Valor médio da fatura estimada solar
    can.drawCentredString(441, 256, f"R$ {f_br(valor_fatura_estimada_solar)}")

    # 19. Retorno Financeiro
    anos_inteiros = math.floor(payback_anos)
    payback_calculo = ((int(payback_meses)) - (int(anos_inteiros) * 12))
    can.drawCentredString(441, 224, f"{int(anos_inteiros)} anos e")
    can.drawCentredString(441, 210, f"{payback_calculo} meses")

    # --- VALOR TOTAL DO ORÇAMENTO (RODAPÉ) ---
    can.setFont("Helvetica-Bold", 36)
    can.setFillColorRGB(1, 1, 1)
    # Aplicando a mesma lógica de formatação aqui
    texto_total = f"R$ {f_br(valor_arredondado)}"
    can.drawRightString(550, 53, texto_total)

    # Finaliza a página 3
    can.showPage()

####### FINAL DO 19.1 ############
def gerar_pdf_completo():
    writer = PdfWriter()
    caminho_capa = r"capa.pdf"
    caminho_fundo_p2 = r"dois.jpg"
    caminho_excel = r"precos_lumo.xlsx"

    try:
        # --- PÁGINA 1: CAPA (PDF Externo + Nome do Cliente) ---
        # --- PÁGINA 1: CAPA (PDF Externo + Nome do Cliente) ---
        if os.path.exists(caminho_capa):
            capa_reader = PdfReader(caminho_capa)
            p1 = capa_reader.pages[0]

            # Criar um novo PDF em memória para o nome do cliente
            packet_capa = io.BytesIO()
            can_capa = canvas.Canvas(packet_capa, pagesize=A4)

            # --- CONFIGURAÇÃO DO NOME (X=310, Y=452, TAM 24, AZUL MARINHO) ---
            nome_cliente = st.session_state.get('nome_cliente_key', '')
            can_capa.setFont("Helvetica-Bold", 24)

            # Definindo a cor Azul Marinho (#002d81)
            can_capa.setFillColorRGB(0.0, 0.176, 0.506)
            can_capa.drawString(43, 442, nome_cliente)

            can_capa.save()
            packet_capa.seek(0)

            # Mesclar o nome com a capa original
            overlay_capa = PdfReader(packet_capa).pages[0]
            p1.merge_page(overlay_capa)
            writer.add_page(p1)


        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        largura_a4, altura_a4 = A4

        # --- PÁGINA 2: DADOS TÉCNICOS E GRÁFICO ---
        if os.path.exists(caminho_fundo_p2):
            can.drawImage(caminho_fundo_p2, 0, 0, width=largura_a4, height=altura_a4)

            # Configurações de Alinhamento (Volta para o original 103)
            X_ALINHAMENTO = 103
            Y_BASE_GRAFICO = 240

            # Resgate de Dados
            qtd_inv = st.session_state.get('qtd_inversores_manual_key', 1) or 1
            pot_inv = st.session_state.get('potencia_key') or st.session_state.get('inversor_selecionado_final', 0)
            marca_inv = st.session_state.get('marca_key', '')
            qtd_mod = int(st.session_state.get('qtd_modulos_final', 0))
            pot_mod_w = float(st.session_state.get('potencia_modulo_final', 0))
            sobra_modulos = st.session_state.get('sobra_modulos_final', 0)

            # --- INSERÇÃO DA DATA ATUAL ---
            data_atual = datetime.now().strftime("%d/%m/%Y")
            can.setFont("Helvetica-Bold", 22)  # Tamanho sugerido para rodapé
            can.setFillColorRGB(1, 1, 1)  # Preto
            can.drawCentredString(470, 22, f"Data {data_atual}")

            # Busca de Garantias no Excel
            garantia_inv, garantia_mod = "10", "12"
            if os.path.exists(caminho_excel):
                try:
                    df_inv = pd.read_excel(caminho_excel, sheet_name="Inversores")
                    filtro_inv = df_inv[(df_inv.iloc[:, 0] == marca_inv) & (df_inv.iloc[:, 1] == pot_inv)]
                    if not filtro_inv.empty: garantia_inv = str(filtro_inv.iloc[0, 4])
                    df_mod_excel = pd.read_excel(caminho_excel, sheet_name="Módulo")
                    filtro_mod = df_mod_excel[df_mod_excel.iloc[:, 0] == marca_inv]
                    if not filtro_mod.empty: garantia_mod = str(filtro_mod.iloc[0, 3])
                except:
                    pass

            # Logo do Inversor (X=20, Y=20, Tamanho 4x)
            caminho_logo = buscar_imagem_logo(marca_inv)
            if caminho_logo:
                can.drawImage(caminho_logo, 20, 20, width=240, height=120, mask='auto', preserveAspectRatio=True)

            # Textos Técnicos
            fonte = "Helvetica-Bold"
            tam = 11
            can.setFont(fonte, tam)
            can.setFillColorRGB(0, 0, 0)
            esp = 5

            # Inversores (Y=603)
            curr_x = X_ALINHAMENTO
            can.drawString(curr_x, 603, f"{qtd_inv}")
            curr_x += stringWidth(f"{qtd_inv}", fonte, tam) + esp
            txt_inv = "Inversor" if qtd_inv == 1 else "Inversores"
            can.drawString(curr_x, 603, txt_inv)
            curr_x += stringWidth(txt_inv, fonte, tam) + esp
            can.drawString(curr_x, 603, f"{pot_inv} kW {marca_inv}")

            # Módulos (Y=563)
            curr_x_m = X_ALINHAMENTO
            can.drawString(curr_x_m, 563, f"{qtd_mod}")
            curr_x_m += stringWidth(f"{qtd_mod}", fonte, tam) + esp
            txt_mod = "Módulo" if qtd_mod == 1 else "Módulos"
            can.drawString(curr_x_m, 563, txt_mod)
            curr_x_m += stringWidth(txt_mod, fonte, tam) + esp
            can.drawString(curr_x_m, 563, f"{int(pot_mod_w)}W")

            # Garantias
            can.drawString(320, 608, f"Inversor com garantia de {garantia_inv} anos.")
            can.drawString(320, 563, f"{txt_mod} com {garantia_mod} anos de garantia.")
            can.drawString(320, 520, "Garantia de 85% de eficiência em 30 anos")

            if sobra_modulos > 0:
                can.drawString(X_ALINHAMENTO, 528, "Inversor com capacidade")
                can.drawString(X_ALINHAMENTO, 512,
                               f"de ampliar {sobra_modulos} {'Módulo' if sobra_modulos == 1 else 'Módulos'}")

            # --- Lógica do Gráfico ---
            ordem_meses = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
            prod_mensal = {"JAN": 0.135, "FEV": 0.111, "MAR": 0.103, "ABR": 0.081, "MAI": 0.072, "JUN": 0.055,
                           "JUL": 0.063, "AGO": 0.077, "SET": 0.087, "OUT": 0.110, "NOV": 0.127, "DEZ": 0.145}
            pot_total_w = float(qtd_mod) * float(pot_mod_w)

            metodo = st.session_state.get('metodo_consumo_key')
            formato_manual = st.session_state.get('formato_consumo_key')
            if metodo == "Leitura de PDF" or (metodo == "Manual" and formato_manual == "Histórico 12 Meses"):
                hist = st.session_state.get('historico_12_meses_key', {})
                v_ex = [float(v) for v in hist.values() if v and float(v) > 0]
                media_c = sum(v_ex) / len(v_ex) if v_ex else 0.0
            else:
                media_c = float(st.session_state.get('consumo_final_key', 0.0))
                hist = {m: media_c for m in ordem_meses}

            largura_grafico = 480
            altura_max_barra = 260
            X_ALINHAMENTO = 57.5
            Y_BASE_GRAFICO = 240
            largura_mes = largura_grafico / 12
            largura_barra = largura_mes * 0.35

            max_valor = 1.0
            for m in ordem_meses:
                max_valor = max(max_valor, float(hist.get(m, media_c)), pot_total_w * prod_mensal[m])
            escala = altura_max_barra / (max_valor * 1.15)

            for i, mes in enumerate(ordem_meses):
                x_mes = X_ALINHAMENTO + (i * largura_mes)
                val_c = float(hist.get(mes, media_c))
                h_c = val_c * escala
                can.setFillColorRGB(0, 0, 0.5)
                can.rect(x_mes, Y_BASE_GRAFICO, largura_barra, h_c, fill=1, stroke=0)
                can.setFont("Helvetica-Bold", 6)
                can.drawCentredString(x_mes + (largura_barra / 2), Y_BASE_GRAFICO + h_c + 3, f"{int(val_c)}")

                val_g = pot_total_w * prod_mensal[mes]
                h_g = val_g * escala
                can.setFillColorRGB(1, 0.65, 0)
                can.rect(x_mes + largura_barra + 2, Y_BASE_GRAFICO, largura_barra, h_g, fill=1, stroke=0)
                can.drawCentredString(x_mes + largura_barra + 2 + (largura_barra / 2), Y_BASE_GRAFICO + h_g + 3,
                                      f"{int(val_g)}")

                can.setFillColorRGB(0, 0, 0)
                can.setFont("Helvetica-Bold", 8)
                can.drawCentredString(x_mes + largura_barra, Y_BASE_GRAFICO - 12, mes)

            # --- LEGENDA CENTRALIZADA ABAIXO DO GRÁFICO ---
            y_legenda = Y_BASE_GRAFICO - 35
            # O ponto central da folha é 297.5. Ajustamos o início para os dois blocos ficarem simétricos.
            x_inicio_legenda = 200

            can.setFillColorRGB(0, 0, 0.5)
            can.rect(x_inicio_legenda, y_legenda, 8, 8, fill=1, stroke=0)
            can.setFillColorRGB(0, 0, 0)
            can.setFont("Helvetica-Bold", 9)
            can.drawString(x_inicio_legenda + 12, y_legenda, "Consumo (kWh)")

            can.setFillColorRGB(1, 0.65, 0)
            can.rect(x_inicio_legenda + 110, y_legenda, 8, 8, fill=1, stroke=0)
            can.setFillColorRGB(0, 0, 0)
            can.drawString(x_inicio_legenda + 122, y_legenda, "Geração (kWh)")

            can.showPage()

        # --- PÁGINA 3 (CHAMA A SEÇÃO 19.1) ---
        renderizar_pagina_3(can)

        can.save()
        packet.seek(0)

        # Consolidação Final
        new_pdf = PdfReader(packet)
        for page in new_pdf.pages:
            writer.add_page(page)

        pdf_buffer = io.BytesIO()
        writer.write(pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer
    except Exception as e:
        st.error(f"Erro na geração do PDF: {e}")
        return None


# --- EXECUÇÃO E DOWNLOAD ---
nome_cliente_raw = st.session_state.get('nome_cliente_key', 'Cliente').strip()
nome_cliente_limpo = re.sub(r'[\\/*?:"<>|]', "", nome_cliente_raw)
qtd_f = float(st.session_state.get('qtd_modulos_final', 0))
pot_f = float(st.session_state.get('potencia_modulo_final', 0))
pot_kwp = (qtd_f * pot_f) / 1000
nome_do_arquivo = f"Orçamento Lumo - {pot_kwp:.2f}KWP {nome_cliente_limpo}.pdf"

pdf_finalizado = gerar_pdf_completo()
if pdf_finalizado:
    st.download_button(
        label="Baixar Orçamento Completo",
        data=pdf_finalizado,
        file_name=nome_do_arquivo,
        mime="application/pdf",
        use_container_width=True
    )


# --- SEÇÃO 20 FUNÇÃO PARA GERAR O PDF DE CUSTOS EM PÁGINA ÚNICA (CORRIGIDA) ---
def gerar_pdf_custos_detalhado():
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    largura, altura = A4

    # Ajuste de margens para caber tudo em uma página
    y = altura - 35

    def draw_header():
        nonlocal y
        can.setFont("Helvetica-Bold", 12)
        can.setFillColor(colors.navy)
        can.drawString(50, y, "RELATÓRIO DE CONFERÊNCIA TÉCNICA E CUSTOS - LUMO ENERGIA")
        y -= 15
        can.setFont("Helvetica", 8)
        can.setFillColor(colors.black)
        can.drawString(50, y,
                       f"Cliente: {st.session_state.get('nome_cliente_key', 'N/A')} | Data: {pd.to_datetime('today').strftime('%d/%m/%Y %H:%M')}")
        y -= 5
        can.line(50, y, 540, y)
        y -= 12

    draw_header()

    def draw_section(titulo):
        nonlocal y
        y -= 5
        can.setFont("Helvetica-Bold", 9)
        can.setFillColor(colors.navy)
        can.drawString(50, y, titulo)
        can.setFillColor(colors.black)
        y -= 11

    def draw_item(label, valor):
        nonlocal y
        can.setFont("Helvetica", 8.5)
        can.drawString(60, y, str(label))
        can.drawRightString(530, y, str(valor))
        y -= 10.5

    # 1. CONFIGURAÇÕES E SOBRAS
    draw_section("1. CONFIGURAÇÕES E PARÂMETROS")
    draw_item("Modo da Usina:", st.session_state.get('modo_usina_key', 'N/A'))
    draw_item("Tipo de Telhado:", st.session_state.get('tipo_telhado_key', 'N/A'))
    draw_item("Cliente Rural:", "Sim" if st.session_state.get('cliente_rural_key') else "Não")
    draw_item("Sobra de Inversor:", f"{st.session_state.get('pc_sobra_inv_key', 0.0)}%")

    sobra_val = st.session_state.get('pc_sobra_geracao_key', 0.0) if st.session_state.get(
        'tipo_sobra_key') == "Porcentagem" else st.session_state.get('kwh_sobra_geracao_key', 0.0)
    sobra_sufixo = "%" if st.session_state.get('tipo_sobra_key') == "Porcentagem" else " kWh"
    draw_item("Sobra de Geração:", f"{sobra_val}{sobra_sufixo}")

    # 2. EQUIPAMENTOS E ESTRUTURA
    draw_section("2. EQUIPAMENTOS E DETALHAMENTO DE ESTRUTURA")
    draw_item("Inversor:",
              f"{st.session_state.get('marca_key', 'N/A')} {st.session_state.get('inversor_selecionado_final', 0)} kW")
    draw_item("Módulos:",
              f"{int(st.session_state.get('qtd_modulos_final', 0))}x {st.session_state.get('marca_modulo_key', 'N/A')} {st.session_state.get('potencia_modulo_final', 0)}W")

    est_detalhe = f"Perfil: {st.session_state.get('pdf_q_perfil', 0)} | T Final: {st.session_state.get('pdf_q_t_final', 0)} | T Interm: {st.session_state.get('pdf_q_t_inter', 0)} | P Estrut: {st.session_state.get('pdf_q_p_estru', 0)}"
    if st.session_state.get('tipo_telhado_key') == "Telha":
        est_detalhe += f" | Sup. Cerâmico: {st.session_state.get('pdf_q_sup_cer', 0)}"
    draw_item("Quantidades de Estrutura:", est_detalhe)

    # 3. PERFORMANCE E GRÁFICO
    draw_section("3. PERFORMANCE MENSAL (kWh)")
    p_w = float(st.session_state.get('qtd_modulos_final', 0)) * float(st.session_state.get('potencia_modulo_final', 0))
    p_ind = [0.1350, 0.1110, 0.1031, 0.0817, 0.0722, 0.0558, 0.0639, 0.0775, 0.0876, 0.1100, 0.1272, 0.1454]
    m_g = (p_w * sum(p_ind)) / 12
    m_c = float(st.session_state.get('consumo_final_key', 0.0))
    draw_item("Médias Mensais:", f"Consumo: {m_c:.1f} kWh | Geração: {m_g:.1f} kWh")

    y -= 5
    x_g = 70
    y_b = y - 50
    esc = 0.03
    ms = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
    h_c = st.session_state.get('historico_12_meses_key', {})

    for i, m in enumerate(ms):
        vc = float(h_c.get(m, m_c));
        vg = p_w * p_ind[i]
        can.setFillColor(colors.navy);
        can.rect(x_g + (i * 38), y_b, 12, vc * esc, fill=1, stroke=0)
        can.setFillColor(colors.orange);
        can.rect(x_g + (i * 38) + 14, y_b, 12, vg * esc, fill=1, stroke=0)
        can.setFont("Helvetica-Bold", 5);
        can.setFillColor(colors.black)
        can.drawCentredString(x_g + (i * 38) + 6, y_b + (vc * esc) + 2, f"{int(vc)}")
        can.drawCentredString(x_g + (i * 38) + 20, y_b + (vg * esc) + 2, f"{int(vg)}")
        can.drawCentredString(x_g + (i * 38) + 13, y_b - 8, m)

    y = y_b - 18

    # 4. COMPOSIÇÃO FINANCEIRA (CORREÇÃO MATERIAL ELÉTRICO)
    draw_section("4. COMPOSIÇÃO FINANCEIRA DETALHADA")
    draw_item("Custo Kit Fotovoltaico:", f"R$ {st.session_state.get('valor_kit_projeto_final', 0.0):,.2f}")
    # BUSCANDO VARIÁVEL CORRETA DA SEÇÃO 13: custo_material_final
    draw_item("Material Elétrico:", f"R$ {st.session_state.get('custo_material_final', 0.0):,.2f}")
    draw_item("Custo Total de Estrutura:", f"R$ {st.session_state.get('custo_estrutura_final', 0.0):,.2f}")
    draw_item("Custo de Instalação:", f"R$ {st.session_state.get('custo_instalacao_final', 0.0):,.2f}")
    draw_item("Custo de Projeto (Engenharia):", f"R$ {st.session_state.get('custo_projeto_final', 0.0):,.2f}")
    draw_item("Cesta de Benefícios:", f"R$ {st.session_state.get('custo_cesta_final', 0.0):,.2f}")
    draw_item("Valor de Indicação:", f"R$ {st.session_state.get('indicacao_valor_calculado', 0.0):,.2f}")
    draw_item("Comissão Representante:", f"R$ {st.session_state.get('valor_representante_final', 0.0):,.2f}")
    draw_item(f"Imposto ({st.session_state.get('imposto_pc_final', 0)}%):",
              f"R$ {st.session_state.get('imposto_valor_calculado', 0.0):,.2f}")
    draw_item("Lucro da Empresa:", f"R$ {st.session_state.get('valor_lucro_final', 0.0):,.2f}")

    y -= 5
    can.setFont("Helvetica-Bold", 10.5);
    can.setFillColor(colors.navy)
    draw_item("VALOR TOTAL FINAL DO ORÇAMENTO:", f"R$ {st.session_state.get('valor_total_final_projeto', 0.0):,.2f}")

    can.save()
    packet.seek(0)
    return packet


# --- BOTÃO DE DOWNLOAD ---
st.write("---")
pdf_custos_final = gerar_pdf_custos_detalhado()
st.download_button(
    label=" BAIXAR RELATÓRIO CUSTOS",
    data=pdf_custos_final,
    file_name=f"Relatorio_Custos_{st.session_state.get('nome_cliente_key', 'Cliente')}.pdf",
    mime="application/pdf",
    use_container_width=True
)