export async function buscarJogosDestaqueKinguin() {
  try {
    const apiKey = import.meta.env.KINGUIN_API_KEY;

    if (apiKey && apiKey !== 'SUA_CHAVE_AQUI') {
      const url = 'https://gateway.kinguin.net/esa/api/v1/products?limit=20&active=true';
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'X-Api-Key': apiKey,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        const listaJogos = data.results || data.data || data;
        if (Array.isArray(listaJogos) && listaJogos.length > 0) {
          return listaJogos.map(game => ({
            name: game.name || game.title,
            price: game.price || game.salePrice || 19.99,
            cover: game.cover || game.image || game.thumbnail || 'https://cdn.cloudflare.steamstatic.com/steam/apps/109150/header.jpg',
            url: game.url || '#'
          }));
        }
      }
    }
  } catch (error) {
    console.error("Aviso: Usando catálogo de destaque Kinguin local.", error);
  }

  // Catálogo com as capas oficiais e originais de cada jogo via CDN direta
  return [
    {
      name: 'EA Sports FC 24 Steam Key',
      price: 89.90,
      cover: 'https://cdn.cloudflare.steamstatic.com/steam/apps/2195250/header.jpg',
      url: '#'
    },
    {
      name: 'Cyberpunk 2077 GOG Key',
      price: 59.99,
      cover: 'https://cdn.cloudflare.steamstatic.com/steam/apps/109150/header.jpg',
      url: '#'
    },
    {
      name: 'Elden Ring Steam Key',
      price: 149.90,
      cover: 'https://cdn.cloudflare.steamstatic.com/steam/apps/1245620/header.jpg',
      url: '#'
    },
    {
      name: 'Red Dead Redemption 2 Rockstar Key',
      price: 69.90,
      cover: 'https://cdn.cloudflare.steamstatic.com/steam/apps/1174180/header.jpg',
      url: '#'
    },
    {
      name: 'Hogwarts Legacy Steam Key',
      price: 99.90,
      cover: 'https://cdn.cloudflare.steamstatic.com/steam/apps/990080/header.jpg',
      url: '#'
    },
    {
      name: 'God of War Steam Key',
      price: 79.90,
      cover: 'https://cdn.cloudflare.steamstatic.com/steam/apps/1593500/header.jpg',
      url: '#'
    }
  ];
}