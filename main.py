import pandas as pd
import requests
import os
import ast
import streamlit as st
from dotenv import load_dotenv
import plotly.express as px

#Edicao de cor e layout da pagina
st.set_page_config(page_title="Dashboard RAWG Games", layout="wide")
st.markdown("""
    <style>
        body {
            background-color: #000000;
            color: #FF0000;
        }
        .stApp {
            background-color: #0d0d0d;
        }
    </style>
""", unsafe_allow_html=True)


st.title("🎮 Dashboard RAWG - Jogos Populares")

#COLETA DE DADOS DA API
#Codigo para consumir dados de uma API no caso de dados de jogos, origem API RAWG.
#Apos solicitar a chave de acesso no site da RAWG, Ela e o acesso para buscar os dados dentro de do sistema

load_dotenv() #Por seguranca da chave"key" gerei um arquivo env para o git ignorar , mais e so voce gerar a sua chave no site e subistituir o comando [os.getenv('chave')] pela sua key gerada.
key = os.getenv('chave_rawg')  #Chave de acesso
url = f'https://api.rawg.io/api/games?key={key}'#Caminho da API no caso a URL, use a funcao formart f para trazer a variavel nos {}, no caso URL + KEY
#Respota da solicitacao dos dados para a api
request = requests.get(url)
#Validador da resposta, apenas uma condicional para retorno do request com o response ! padrao resposta 200
if request.status_code != 200:
    st.error(f"Erro ao acessar a API: {request.status_code}")
    st.stop()
#Armazena os doados da resposta 200 na variavel dados no formato de json
response = request.json()
req = response['results']
rawg_api = pd.json_normalize(req)


#Para trazer todas as colunas para visualizacao
pd.set_option('display.max_columns', 40)

#Visualizar as 5 primeiras/ultimas linhas / e verificar as informacoes de tipo de dados e colunas 
rawg_api.head(2)
#tabela.tail()
#tabela.info()
rawg_api.columns

# Limpeza e seleção de dados
# =============================
df = rawg_api[['id', 'slug', 'name', 'released','rating','rating_top', 'ratings', 'updated',  'platforms','genres']]
df.rename(columns={'id': 'game_id'}, inplace=True)

# Extrações

#identifiquei que tem dados em celulas no formato lista/str
#Funcao para extrair os dados e transformar em dataframe
def extrair_coluna(df, coluna):
    df_temp = df[['id', coluna]].copy()
    df_temp[coluna] = df_temp[coluna].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    df_explodido = df_temp.explode(coluna).reset_index(drop=True)
    df_normalizado = pd.json_normalize(df_explodido[coluna])
    df_resultado = pd.concat([df_explodido[['id']], df_normalizado], axis=1)
    return df_resultado


# Extrações apos a funccao
platforms = extrair_coluna(rawg_api, 'platforms')
platforms.rename(columns={'platform.name': 'platform_name'}, inplace=True)
platforms = platforms[['id', 'released_at', 'platform_name']]
platforms.rename(columns={'id': 'game_id'}, inplace=True)

genres = extrair_coluna(rawg_api, 'genres')
genres = genres[['id','name']]
genres.rename(columns={'id': 'game_id', 'name': 'genre'}, inplace=True)

# Conversão de datas
df['released'] = pd.to_datetime(df['released'])
df['updated'] = pd.to_datetime(df['updated'])
platforms['released_at'] = pd.to_datetime(platforms['released_at'])

#Definicao dos KPI para analise
total_games = df['game_id'].nunique()
cla_media = round(df['rating'].mean(), 2)
ultimo_lanc = df['released'].max().date()
jogos_ano = df['released'].dt.year.value_counts().sort_index()
jogos_plata = platforms.groupby('platform_name')['game_id'].nunique().sort_values(ascending=False)


#Dashboard e graficos dos KPI

col1, col2, col3 = st.columns(3)
col1.metric("Total de Jogos", total_games)
col2.metric("Média de Avaliação", cla_media)
col3.metric("Lançamento Mais Recente", str(ultimo_lanc))

st.markdown("---")

#Gráfico de Jogos por Ano
fig1 = px.bar(
    jogos_ano,
    x=jogos_ano.index,
    y=jogos_ano.values,
    labels={'x': 'Ano de Lançamento', 'y': 'Quantidade de Jogos'},
    title="🎯 Jogos Lançados por Ano",
    color_discrete_sequence=['red']
)
st.plotly_chart(fig1, use_container_width=True)

#Gráfico de Jogos por Plataforma
fig2 = px.bar(
    jogos_plata.head(10),
    x=jogos_plata.head(10).values,
    y=jogos_plata.head(10).index,
    orientation='h',
    labels={'x': 'Número de Jogos', 'y': 'Plataforma'},
    title="🎮 Top 10 Plataformas com Mais Jogos",
    color_discrete_sequence=['red']
)
st.plotly_chart(fig2, use_container_width=True)

#Tabela
st.markdown("---")
st.subheader("📋 Tabela de Jogos")

st.dataframe(df[['name', 'released', 'rating', 'rating_top']].sort_values(by='released', ascending=False))