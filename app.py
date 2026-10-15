import streamlit as st
import sqlite3
import requests
import pandas as pd
import re
from PIL import Image
import os
import shutil

try:
    import pytesseract
    caminhos_possiveis = [
        r'C:\tesseract-ocr\tesseract.exe',
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        shutil.which('tesseract')
    ]
    encontrou = False
    for caminho in caminhos_possiveis:
        if caminho and os.path.exists(str(caminho)):
            pytesseract.pytesseract.tesseract_cmd = caminho
            encontrou = True
            break
    OCR_ATIVO = encontrou
except ImportError:
    OCR_ATIVO = False

st.set_page_config(page_title="Organizador de Afiliados IA", page_icon="🤖", layout="wide")

def init_db():
    conn = sqlite3.connect("afiliados.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            marketplace TEXT,
            link TEXT UNIQUE,
            preco TEXT,
            preco_normal TEXT,
            desconto INTEGER,
            imagem_url TEXT,
            preview_video TEXT,
            modal_video TEXT,
            status TEXT
        )
    ''')
    for col, tipo in [
        ('preco_normal', 'TEXT'), 
        ('desconto', 'INTEGER'), 
        ('imagem_url', 'TEXT'),
        ('preview_video', 'TEXT'),
        ('modal_video', 'TEXT')
    ]:
        try:
            cursor.execute(f"ALTER TABLE produtos ADD COLUMN {col} {tipo}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()

init_db()

st.title("🤖 Organizador Inteligente com Categorias, Imagens & Upload de Vídeos")
st.markdown("Cole o texto da oferta, selecione a categoria, envie as imagens e os arquivos de vídeo para gerar o JSON perfeito.")

# Dicionário de pastas e géneros correspondentes para o site Astro
categorias_map = {
    "tvs": "TVs / 4K",
    "consoles": "Consoles",
    "geladeiras": "Geladeiras",
    "jogos": "Jogos Mídia Física",
    "maquina-de-lavar": "Máquina de Lavar",
    "robo-aspirador": "Robô Aspirador",
    "ar-condicionado": "Ar-Condicionado",
    "air-fryer": "Air Fryer",
    "panela-de-arroz": "Panela de Arroz Elétrica",
    "micro-ondas": "Micro-Ondas",
    "liquidificador": "Liquidificador",
    "utensilios-cozinha": "Utensílios de Cozinha",
    "celulares": "Celulares",
    "fones-de-ouvido": "Fones de Ouvido",
    "cama-mesa-banho": "Cama, Mesa e Banho",
    "cadeiras-gamers": "Cadeiras Gamers",
    "eletronicos": "Eletrônicos em Geral"
}

with st.expander("⚡ Colagem Rápida de Textos, Links de Imagens e Upload de Vídeos", expanded=True):
    texto_copiado = st.text_area("1. Cole aqui o texto copiado da página do produto (Título, Preços, etc.):", height=90)
    links_imagens_colados = st.text_area("2. Cole aqui os links das imagens (um por linha ou separados por vírgula):", placeholder="https://...webp\nhttps://...webp", height=70)
    
    st.markdown("---")
    st.markdown("🎥 **Envio de Vídeos (caso não consiga baixar por link direto do Mercado Livre):**")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        arquivo_preview = st.file_uploader("3. Vídeo de Amostra (Hover do Card - .mp4)", type=["mp4", "webm"], key="up_preview")
    with col_v2:
        arquivo_modal = st.file_uploader("4. Vídeo Completo (Modal - .mp4)", type=["mp4", "webm"], key="up_modal")

    auto_titulo = ""
    auto_preco = ""
    auto_preco_normal = ""
    auto_desconto = 0

    if texto_copiado:
        linhas = [l.strip() for l in texto_copiado.split('\n') if l.strip()]
        if linhas:
            auto_titulo = max(linhas, key=len) if linhas else ""
        
        precos = re.findall(r'R\$\s*[\d\.,]+', texto_copiado.replace('\n', ' '))
        if len(precos) >= 2:
            auto_preco_normal = precos[0]
            auto_preco = precos[1]
        elif len(precos) == 1:
            auto_preco = precos[0]

        descontos = re.findall(r'(\d+)%\s*OFF', texto_copiado, re.IGNORECASE)
        if descontos:
            auto_desconto = int(descontos[0])

st.divider()
st.subheader("➕ Registar Produto e Gerar Código JSON")

with st.form("form_produto"):
    col1, col2 = st.columns(2)
    
    with col1:
        titulo = st.text_input("Título / Nome do Produto", value=auto_titulo)
        marketplace = st.selectbox("Marketplace", ["Mercado Livre", "Amazon", "Kinguin", "Shopee", "Outro"])
        link = st.text_input("Link de Afiliado (URL completa)")
        
        sub_pasta = st.selectbox(
            "Pasta de Destino em `public/` & Categoria", 
            options=list(categorias_map.keys()),
            format_func=lambda x: f"{x} ➔ Género: {categorias_map[x]}"
        )
    
    with col2:
        preco_input = st.text_input("Preço Atual (ex: R$ 4.928,07)", value=auto_preco)
        preco_normal_input = st.text_input("Preço Normal / Anterior (ex: R$ 5.299)", value=auto_preco_normal)
        desconto = st.number_input("Desconto (%)", value=auto_desconto, min_value=0, max_value=100)
        
    submitted = st.form_submit_button("Processar Links e Guardar Produto")
    
    if submitted:
        if not link or not titulo:
            st.error("⚠️ Preencha pelo menos o Título e o Link de Afiliado!")
        else:
            base_public = os.path.join("public", sub_pasta)
            os.makedirs(base_public, exist_ok=True)
            slug_nome = re.sub(r'[^a-z0-9]+', '-', titulo.lower()).strip('-')
            
            # Processamento de Imagens
            caminhos_imagens = []
            if links_imagens_colados:
                urls_imgs = re.split(r'[\n,]+', links_imagens_colados)
                for idx, url_img in enumerate(urls_imgs, start=1):
                    url_limpa = url_img.strip()
                    if url_limpa.startswith("http"):
                        try:
                            headers = {'User-Agent': 'Mozilla/5.0'}
                            response = requests.get(url_limpa, headers=headers, timeout=10)
                            if response.status_code == 200:
                                ext = ".webp"
                                if ".jpg" in url_limpa or ".jpeg" in url_limpa:
                                    ext = ".jpg"
                                elif ".png" in url_limpa:
                                    ext = ".png"
                                
                                nome_ficheiro = f"{slug_nome}-{idx}{ext}"
                                caminho_fisico = os.path.join(base_public, nome_ficheiro)
                                with open(caminho_fisico, "wb") as f:
                                    f.write(response.content)
                                caminhos_imagens.append(f"/{sub_pasta}/{nome_ficheiro}")
                        except Exception:
                            pass

            # Salvando o Vídeo de Amostra (Hover) enviado por Upload
            caminho_preview_final = ""
            if arquivo_preview is not None:
                nome_v1 = f"{slug_nome}-preview.mp4"
                caminho_fisico_v1 = os.path.join(base_public, nome_v1)
                with open(caminho_fisico_v1, "wb") as f:
                    f.write(arquivo_preview.getbuffer())
                caminho_preview_final = f"/{sub_pasta}/{nome_v1}"

            # Salvando o Vídeo do Modal enviado por Upload
            caminho_modal_final = ""
            if arquivo_modal is not None:
                nome_v2 = f"{slug_nome}-trailer.mp4"
                caminho_fisico_v2 = os.path.join(base_public, nome_v2)
                with open(caminho_fisico_v2, "wb") as f:
                    f.write(arquivo_modal.getbuffer())
                caminho_modal_final = f"/{sub_pasta}/{nome_v2}"

            string_caminhos = ",".join(caminhos_imagens) if caminhos_imagens else ""
            preco_limpo = preco_input.replace('\n', ' ').strip()
            preco_normal_limpo = preco_normal_input.replace('\n', ' ').strip()

            try:
                conn = sqlite3.connect("afiliados.db")
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO produtos 
                    (titulo, marketplace, link, preco, preco_normal, desconto, imagem_url, preview_video, modal_video, status) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (titulo, marketplace, link, preco_limpo, preco_normal_limpo, desconto, string_caminhos, caminho_preview_final, caminho_modal_final, "Ativo")
                )
                conn.commit()
                conn.close()
                st.success(f"✅ Produto registado com sucesso na pasta `public/{sub_pasta}`!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.warning("⚠️ Este link de afiliado já está registado na base de dados!")

st.divider()
st.subheader("📦 Produtos Guardados & Códigos JSON")

conn = sqlite3.connect("afiliados.db")
df = pd.read_sql("SELECT * FROM produtos ORDER BY id DESC", conn)
conn.close()

if not df.empty:
    pesquisa = st.text_input("🔍 Pesquisar produtos guardados...", "")
    if pesquisa:
        df = df[df['titulo'].str.contains(pesquisa, case=False, na=False)]

    for index, row in df.iterrows():
        with st.container():
            cols = st.columns([1, 3, 2])
            
            lista_imgs = [img.strip() for img in str(row['imagem_url']).split(',') if img.strip()]
            primeira_img = lista_imgs[0] if lista_imgs else ""
            
            img_exibicao = primeira_img
            if img_exibicao.startswith('/'):
                img_exibicao = os.path.join("public", img_exibicao.lstrip('/'))
            if not img_exibicao or not os.path.exists(str(img_exibicao)):
                img_exibicao = "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=200&auto=format&fit=crop"

            cols[0].image(img_exibicao, width=90)
            
            tem_preview = "Sim" if row.get('preview_video') else "Não"
            tem_modal = "Sim" if row.get('modal_video') else "Não"
            
            cols[1].markdown(f"**{row['titulo']}** \n\n`{row['marketplace']}` | **{row['preco']}** (-{row['desconto']}%) \n\n📸 Imagens: {len(lista_imgs)} | 🎬 Preview Hover: `{tem_preview}` | 🎥 Vídeo Modal: `{tem_modal}`")
            
            genre_detectado = "Eletrônicos em Geral"
            for pasta, genero in categorias_map.items():
                if primeira_img.startswith(f"/{pasta}/"):
                    genre_detectado = genero
                    break

            json_imagens_array = ",\n".join([f'        "{img}"' for img in lista_imgs])
            p_atual = str(row['preco']).replace('\n', ' ')
            p_normal = str(row['preco_normal']).replace('\n', ' ')
            v_preview = str(row.get('preview_video') or '')
            v_modal = str(row.get('modal_video') or '')
            
            json_pronto = f"""{{
  "id": "produto-{row['id']}",
  "nome": "{row['titulo']}",
  "preco": "{p_atual}",
  "precoNormal": "{p_normal}",
  "desconto": {row['desconto']},
  "images": [
{json_imagens_array}
  ],
  "previewVideo": "{v_preview}",
  "modalVideo": "{v_modal}",
  "linkBase": "{row['link']}",
  "genre": "{genre_detectado}",
  "ano": 2026,
  "marketplace": "{row['marketplace']}"
}}"""
            
            cols[2].text_area(f"Código JSON (ID {row['id']}):", value=json_pronto, height=190, key=f"json_{row['id']}")
            
            if st.button("Eliminar Produto", key=f"del_{row['id']}"):
                conn = sqlite3.connect("afiliados.db")
                conn.execute("DELETE FROM produtos WHERE id = ?", (row['id'],))
                conn.commit()
                conn.close()
                st.rerun()
            st.divider()
else:
    st.info("Ainda não há produtos guardados. Comece a registar acima!")