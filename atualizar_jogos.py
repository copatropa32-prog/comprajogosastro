import json
import os
import unicodedata
from difflib import get_close_matches

ARQUIVO_JSON = 'src/data/jogos.json'
PASTA_CAPAS = 'public/capas'

def normalizar(texto):
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

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

    # Mapeia os arquivos reais que existem na pasta public/capas
    arquivos_reais = os.listdir(PASTA_CAPAS)
    mapa_arquivos = {normalizar(os.path.splitext(arq)[0]): arq for arq in arquivos_reais}
    chaves_arquivos = list(mapa_arquivos.keys())

    alteracoes = 0
    for jogo in jogos:
        nome_jogo = jogo.get('nome', '')
        if not nome_jogo:
            continue

        nome_norm = normalizar(nome_jogo)
        capa_encontrada = None
        
        # 1. Procura correspondência direta
        for chave in chaves_arquivos:
            if chave in nome_norm or nome_norm in chave:
                capa_encontrada = f"/capas/{mapa_arquivos[chave]}"
                break
        
        # 2. Procura por aproximação
        if not capa_encontrada and chaves_arquivos:
            matches = get_close_matches(nome_norm, chaves_arquivos, n=1, cutoff=0.35)
            if matches:
                melhor_match = matches[0]
                capa_encontrada = f"/capas/{mapa_arquivos[melhor_match]}"

        # Se encontrou o arquivo real, padroniza as chaves 'image' e 'capa'
        if capa_encontrada:
            if jogo.get('image') != capa_encontrada:
                jogo['image'] = capa_encontrada
                alteracoes += 1
            if jogo.get('capa') != capa_encontrada:
                jogo['capa'] = capa_encontrada
                alteracoes += 1
        else:
            # Se não achou arquivo correspondente, limpa os campos para evitar 404
            if jogo.get('image') and "public/" in jogo.get('image', ''):
                jogo['image'] = ""
                alteracoes += 1
            if jogo.get('capa') and "public/" in jogo.get('capa', ''):
                jogo['capa'] = ""
                alteracoes += 1

    if alteracoes > 0:
        with open(ARQUIVO_JSON, 'w', encoding='utf-8') as f:
            json.dump(jogos, f, ensure_ascii=False, indent=4)
        print(f"Sucesso! {alteracoes} ajustes aplicados nos caminhos de imagens do jogos.json.")
    else:
        print("Nenhuma alteração necessária.")

if __name__ == '__main__':
    atualizar_base_jogos()