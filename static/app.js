const $ = (id) => document.getElementById(id);
const message = (text, error = false) => { $('message').textContent = text; $('message').className = error ? 'error' : ''; };
async function api(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Não foi possível concluir a operação.');
  return data;
}
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function card(pokemon, saved) {
  const node = element('article', undefined, 'card');
  node.append(element('span', '#' + String(pokemon.id).padStart(3, '0'), 'number'));
  if (pokemon.image) {
    const img = document.createElement('img'); img.src = pokemon.image;
    img.alt = pokemon.name; img.loading = 'lazy'; node.append(img);
  }
  node.append(element('h3', pokemon.name));
  const types = element('div', undefined, 'types');
  pokemon.types.forEach(type => types.append(element('span', type, 'type'))); node.append(types);
  node.append(element('p', `${pokemon.height / 10} m de altura · ${pokemon.weight / 10} kg`, 'details'));
  const button = element('button', saved ? 'Remover favorito' : '♡ Salvar nos favoritos', saved ? 'remove' : 'save');
  button.type = 'button';
  button.addEventListener('click', async () => {
    button.disabled = true;
    try {
      if (saved) {
        await api('/api/favorites/' + pokemon.id, { method: 'DELETE' });
        message('Pokémon removido da coleção.');
      } else {
        const data = await api('/api/favorites', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: String(pokemon.id) }) });
        message(data.created ? 'Pokémon salvo na sua coleção!' : 'Esse Pokémon já está nos favoritos.');
      }
      await loadFavorites();
    } catch (error) { message(error.message, true); }
    finally { button.disabled = false; }
  }); node.append(button); return node;
}
async function loadFavorites() {
  const favorites = await api('/api/favorites');
  $('count').textContent = `${favorites.length} Pokémon`;
  $('favorites').replaceChildren(...favorites.map(p => card(p, true)));
  if (!favorites.length) $('favorites').append(element('div', 'Sua coleção começa aqui. Busque um Pokémon e salve seu primeiro favorito.', 'empty'));
}
async function search(query) {
  $('search-button').disabled = true; message('Buscando na PokéAPI…'); $('result').replaceChildren();
  try {
    const pokemon = await api('/api/pokemon?q=' + encodeURIComponent(query));
    $('result').append(card(pokemon, false)); message('Encontramos! Você pode salvar este Pokémon.');
  } catch (error) { message(error.message, true); }
  finally { $('search-button').disabled = false; }
}
$('search').addEventListener('submit', event => { event.preventDefault(); search($('query').value); });
document.querySelectorAll('[data-query]').forEach(button => button.addEventListener('click', () => {
  if ($('search-button').disabled) return;
  $('query').value = button.dataset.query; search(button.dataset.query);
}));
loadFavorites().catch(error => message(error.message, true));
