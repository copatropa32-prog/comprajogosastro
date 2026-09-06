import json
import os
import unicodedata

ARQUIVO_JSON = 'src/data/jogos.json'
PASTA_CAPAS = 'public/capas'

def normalizar(texto):
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    limpo = "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()
    apenas_validos = "".join([c if c.isalnum() else '-' for c in limpo])
    while '--' in apenas_validos:
        apenas_validos = apenas_validos.replace('--', '-')
    return apenas_validos.strip('-')

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

    # Mapeia todos os arquivos reais da pasta
    arquivos_reais = os.listdir(PASTA_CAPAS)
    mapa_arquivos = {}
    for arq in arquivos_reais:
        nome_base, ext = os.path.splitext(arq)
        if ext.lower() in ['.webp', '.jpg', '.png', '.avif']:
            mapa_arquivos[normalizar(nome_base)] = arq

    alteracoes = 0

    for i, jogo in enumerate(jogos):
        # Tenta pegar o nome do jogo por várias chaves comuns
        nome_jogo = jogo.get('nome') or jogo.get('title') or jogo.get('titulo') or ''
        if not nome_jogo:
            continue

        nome_norm = normalizar(nome_jogo)
        capa_encontrada = None

        # 1. Correspondência exata do nome normalizado
        if nome_norm in mapa_arquivos:
            capa_encontrada = f"/capas/{mapa_arquivos[nome_norm]}"
        else:
            # 2. Busca inteligente por palavras-chave contidas no nome do arquivo
            melhor_match = None
            maior_pontuacao = 0
            palavras_jogo = set(nome_norm.split('-'))
            
            for chave_norm, nome_arq in mapa_arquivos.items():
                palavras_arquivo = set(chave_norm.split('-'))
                # Conta quantas palavras do jogo batem com o arquivo
                intersecao = palavras_jogo.intersection(palavras_arquivo)
                pontuacao = len(intersecao)
                
                if pontuacao > maior_pontuacao and pontuacao >= max(1, len(palavras_jogo) // 2):
                    maior_pontuacao = pontuacao
                    melhor_match = nome_arq

            if melhor_match:
                capa_encontrada = f"/capas/{melhor_match}"

        if capa_encontrada:
            # Procura dinamicamente por qualquer chave no JSON que pareça ser de imagem/capa
            for chave in list(jogo.keys()):
                chave_lower = chave.lower()
                if any(termo in chave_lower for termo in ['img', 'capa', 'image', 'banner', 'poster', 'photo']):
                    # Se o valor atual for string (ou vazio/quebrado), atualiza
                    if isinstance(jogo.get(chave), (str, type(None))):
                        if jogo.get(chave) != capa_encontrada:
                            jogo[chave] = capa_encontrada
                            alteracoes += 1

    if alteracoes > 0:
        with open(ARQUIVO_JSON, 'w', encoding='utf-8') as f:
            json.dump(jogos, f, ensure_ascii=False, indent=4)
        print(f"Sucesso! {alteracoes} correções aplicadas no {ARQUIVO_JSON}.")
    else:
        print("Nenhuma alteração necessária. Tudo sincronizado!")

if __name__ == '__main__':
    atualizar_base_jogos()