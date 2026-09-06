import json
import os
import unicodedata
from difflib import get_close_matches

ARQUIVO_JSON = 'src/data/jogos.json'
PASTA_CAPAS = 'public/capas'

def normalizar(texto):
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()

def atualizar_base_jogos():
    if not os.path.exists(ARQUIVO_JSON):
        print(f"Erro: {ARQUIVO_JSON} não encontrado.")
        return
    
    with open(ARQUIVO_JSON, 'r', encoding='utf-8') as f:
        try:
            jogos = json.load(f)
        except json.JSONDecodeError:
            print("Erro ao decodificar JSON.")
            return

    if not os.path.exists(PASTA_CAPAS):
        print(f"Pasta {PASTA_CAPAS} não encontrada.")
        return

    # Mapeia os arquivos reais na pasta public/capas
    arquivos_reais = os.listdir(PASTA_CAPAS)
    mapa_arquivos = {}
    for arq in arquivos_reais:
        nome_base, ext = os.path.splitext(arq)
        if ext.lower() in ['.webp', '.jpg', '.png', '.avif']:
            mapa_arquivos[normalizar(nome_base)] = arq

    chaves_arquivos = list(mapa_arquivos.keys())
    alteracoes = 0
    chaves_imagem = ['image', 'capa', 'banner', 'carrossel', 'blockbuster', 'imagem']

    for jogo in jogos:
        nome_jogo = jogo.get('nome', '')
        if not nome_jogo:
            continue

        nome_norm = normalizar(nome_jogo)
        capa_encontrada = None
        
        # 1. Procura correspondência exata ou parcial
        for chave in chaves_arquivos:
            if nome_norm == chave or nome_norm in chave or chave in nome_norm:
                capa_encontrada = f"/capas/{mapa_arquivos[chave]}"
                break
        
        # 2. Procura por aproximação via difflib
        if not capa_encontrada and chaves_arquivos:
            matches = get_close_matches(nome_norm, chaves_arquivos, n=1, cutoff=0.4)
            if matches:
                melhor_match = matches[0]
                capa_encontrada = f"/capas/{mapa_arquivos[melhor_match]}"

        # Aplica ou limpa as chaves de imagem
        for campo in chaves_imagem:
            if campo in jogo:
                valor_atual = jogo.get(campo, '')
                if capa_encontrada:
                    if valor_atual != capa_encontrada:
                        jogo[campo] = capa_encontrada
                        alteracoes += 1
                else:
                    if valor_atual:
                        jogo[campo] = ""  # Evita string suja/URL quebrada gerando 404
                        alteracoes += 1

    if alteracoes > 0:
        with open(ARQUIVO_JSON, 'w', encoding='utf-8') as f:
            json.dump(jogos, f, ensure_ascii=False, indent=4)
        print(f"Sucesso! {alteracoes} ajustes aplicados no {ARQUIVO_JSON}.")
    else:
        print("Nenhuma alteração necessária.")

if __name__ == '__main__':
    atualizar_base_jogos()