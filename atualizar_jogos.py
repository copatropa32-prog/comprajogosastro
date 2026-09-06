import json
import os
import unicodedata

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

    alteracoes = 0
    chaves_imagem = ['image', 'capa', 'banner', 'carrossel', 'blockbuster', 'imagem']

    for jogo in jogos:
        nome_jogo = jogo.get('nome', '')
        if not nome_jogo:
            continue

        nome_norm = normalizar(nome_jogo)
        palavras_jogo = set(nome_norm.split())
        capa_encontrada = None
        
        # 1. Procura correspondência exata ou por inclusão exata
        for chave_norm, nome_arq in mapa_arquivos.items():
            if nome_norm == chave_norm or nome_norm in chave_norm or chave_norm in nome_norm:
                capa_encontrada = f"/capas/{nome_arq}"
                break
        
        # 2. Procura por interseção de palavras relevantes (evita falsos positivos)
        if not capa_encontrada and palavras_jogo:
            melhor_qtd = 0
            for chave_norm, nome_arq in mapa_arquivos.items():
                palavras_chave = set(chave_norm.split())
                comuns = palavras_jogo.intersection(palavras_chave)
                # Se houver pelo menos 2 palavras em comum (ou 1 se o nome for curto)
                if len(comuns) > melhor_qtd and (len(comuns) >= 2 or len(palavras_jogo) == 1):
                    melhor_qtd = len(comuns)
                    capa_encontrada = f"/capas/{nome_arq}"

        # Aplica a imagem encontrada apenas se houver sucesso
        if capa_encontrada:
            for campo in chaves_imagem:
                if campo in jogo:
                    valor_atual = jogo.get(campo, '')
                    if valor_atual != capa_encontrada:
                        jogo[campo] = capa_encontrada
                        alteracoes += 1

    if alteracoes > 0:
        with open(ARQUIVO_JSON, 'w', encoding='utf-8') as f:
            json.dump(jogos, f, ensure_ascii=False, indent=4)
        print(f"Sucesso! {alteracoes} ajustes aplicados no {ARQUIVO_JSON}.")
    else:
        print("Nenhuma alteração necessária.")

if __name__ == '__main__':
    atualizar_base_jogos()