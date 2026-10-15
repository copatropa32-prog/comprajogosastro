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

    # 1. MAPEIA AS CAPAS DA PASTA PRIMEIRO (Priorizando .webp)
    arquivos_reais = os.listdir(PASTA_CAPAS)
    mapa_capas = {}
    
    # Ordena para garantir que .webp sobrescreva formatos antigos caso existam duplicados
    extensoes_prioridade = {'.avif': 1, '.jpg': 2, '.png': 3, '.webp': 4}
    arquivos_reais.sort(key=lambda x: extensoes_prioridade.get(os.path.splitext(x)[1].lower(), 0))

    for arq in arquivos_reais:
        nome_base, ext = os.path.splitext(arq)
        ext_lower = ext.lower()
        if ext_lower in ['.webp', '.jpg', '.png', '.avif']:
            chave_norm = normalizar(nome_base)
            if chave_norm not in mapa_capas or ext_lower == '.webp':
                mapa_capas[chave_norm] = arq

    alteracoes = 0

    # Cria um dicionário auxiliar para mapear o nome normalizado do jogo para o índice dele no JSON
    jogos_por_nome = {}
    for i, jogo in enumerate(jogos):
        nome_jogo = jogo.get('nome') or jogo.get('title') or jogo.get('titulo') or ''
        if nome_jogo:
            jogos_por_nome[normalizar(nome_jogo)] = i

    # 2. PERCORRE AS CAPAS ENCONTRADAS E ATRIBUI AO JOGO CORRESPONDENTE
    for capa_norm, arquivo_capa in mapa_capas.items():
        caminho_final = f"/capas/{arquivo_capa}"
        
        # Procura correspondência exata do nome da capa com o nome do jogo
        indice_jogo = None
        if capa_norm in jogos_por_nome:
            indice_jogo = jogos_por_nome[capa_norm]
        else:
            # Busca aproximada segura (se o nome da capa contiver partes do jogo ou vice-versa)
            for j_norm, idx in jogos_por_nome.items():
                palavras_capa = set(capa_norm.split('-'))
                palavras_jogo = set(j_norm.split('-'))
                if palavras_capa and palavras_capa.issubset(palavras_jogo) and len(palavras_capa) >= 2:
                    indice_jogo = idx
                    break

        if indice_jogo is not None:
            jogo = jogos[indice_jogo]
            # Atualiza todas as chaves de imagem/capa encontradas no objeto do jogo
            for chave in list(jogo.keys()):
                chave_lower = chave.lower()
                if any(termo in chave_lower for termo in ['img', 'capa', 'image', 'banner', 'poster', 'photo']):
                    if jogo.get(chave) != caminho_final:
                        jogo[chave] = caminho_final
                        alteracoes += 1

    if alteracoes > 0:
        with open(ARQUIVO_JSON, 'w', encoding='utf-8') as f:
            json.dump(jogos, f, ensure_ascii=False, indent=4)
        print(f"Sucesso! {alteracoes} capas sincronizadas e atualizadas no {ARQUIVO_JSON}.")
    else:
        print("Nenhuma alteração necessária. Tudo sincronizado!")

if __name__ == '__main__':
    atualizar_base_jogos()