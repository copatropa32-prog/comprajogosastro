import type { APIRoute } from 'astro';
import jogos from '../data/jogos.json';

export const GET: APIRoute = async ({ site }) => {
  const siteUrl = site ? site.toString() : 'https://comprajogos.com.br/';

  const itemsXml = jogos.map(jogo => {
    // Formata o preço para o padrão exigido pelo Google (ex: "179.78 BRL")
    const cleanPrice = (priceStr: string) => {
      const num = priceStr
        .replace('R$', '')
        .trim()
        .replace(/\./g, '')
        .replace(',', '.');
      return `${num} BRL`;
    };

    const precoAtual = cleanPrice(jogo.preco);
    const precoOriginal = cleanPrice(jogo.precoNormal);
    const isDesconto = jogo.desconto > 0;

    // Garante que a URL da imagem seja absoluta
    const imageUrl = jogo.image.startsWith('http') 
      ? jogo.image 
      : `${siteUrl.replace(/\/$/, '')}${jogo.image}`;

    return `
    <item>
      <g:id>${encodeURIComponent(jogo.nome)}</g:id>
      <title><![CDATA[${jogo.nome}]]></title>
      <link>${jogo.linkBase}</link>
      <description><![CDATA[Compre ${jogo.nome} pelo melhor preço. Gênero: ${jogo.genre}.]]></description>
      <g:price>${precoOriginal}</g:price>
      ${isDesconto ? `<g:sale_price>${precoAtual}</g:sale_price>` : ''}
      <g:condition>new</g:condition>
      <g:availability>in stock</g:availability>
      <g:image_link>${imageUrl}</g:image_link>
      <g:brand>Digital / Parceiros</g:brand>
      <g:product_type><![CDATA[Jogos / ${jogo.genre}]]></g:product_type>
    </item>`;
  }).join('');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">
  <channel>
    <title>Compra Jogos - Feed de Produtos</title>
    <link>${siteUrl}</link>
    <description>Catálogo de jogos e ofertas do Compra Jogos</description>
    ${itemsXml}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8'
    }
  });
};