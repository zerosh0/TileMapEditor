  let allNodes = [];

  // Fonction de délai (debounce)
  function debounce(func, delay) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), delay);
    };
  }

  // Charger les nœuds depuis le JSON
  async function loadJSON() {
    const res = await fetch('../assets/nodes.json');
    allNodes = await res.json();
  }

  // Afficher les résultats filtrés (avec limite)
function renderResults(filtered) {
  const MAX_RESULTS = 4;

  const listContainer = document.getElementById('node-list');
  const container = document.getElementById('nodes-container');
  listContainer.innerHTML = '';
  container.innerHTML = '';

  // Aucun résultat
  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <img src="../assets/images/sleep.gif" alt="Aucun nœud trouvé"/>
        <p>Aucun résultat trouvé.</p>
      </div>`;
    return;
  }

  // Limiter les résultats affichés
  const shown = filtered.slice(0, MAX_RESULTS);
  const remaining = filtered.length - shown.length;

  // Grouper par catégorie
  const byCat = shown.reduce((acc, node) => {
    (acc[node.category] = acc[node.category] || []).push(node);
    return acc;
  }, {});

  for (const [cat, nodes] of Object.entries(byCat)) {
    const group = document.createElement('div');
    group.className = 'category-group';
    const header = document.createElement('div');
    header.className = 'category-header';
    header.textContent = cat;
    group.appendChild(header);

    const ul = document.createElement('ul');
    nodes.forEach(node => {
      const li = document.createElement('li');
      li.innerHTML = `<a href="#${node.name}">${node.name}</a>`;
      ul.appendChild(li);
    });

    group.appendChild(ul);
    listContainer.appendChild(group);

    // Générer les cartes dans le container principal
    nodes.forEach(node => {
      const card = document.createElement('div');
      card.className = 'node-card';
      card.id = node.name;
      card.innerHTML = `
        <h2>${node.name}</h2>
        <div class="node-meta">
          <em>${node.category}</em> &middot; <small>${node.source}</small>
        </div>
        <p>${node.description}</p>
        <h3>Pins</h3>
        <ul>${node.pins.map(p =>
          `<li><strong>${p.direction.toUpperCase()}</strong> - ${p.label} <code>(${p.type})</code></li>`
        ).join('')}</ul>
        <h3>Propriétés</h3>
        <ul>${node.properties.map(prop =>
          `<li><code>${prop}</code></li>`
        ).join('')}</ul>
        <h3>Extrait de code</h3>
        <pre class="language-python"><code>${node.code
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
        }</code></pre>
      `;
      container.appendChild(card);
    });
  }

  // Si des résultats sont masqués
  if (remaining > 0) {
    // Message dans le panneau gauche (node-list)
    const infoItem = document.createElement('li');
    infoItem.style.marginTop = '1rem';
    infoItem.style.color = '#666';
    infoItem.style.fontStyle = 'italic';
    infoItem.textContent = `${remaining} nœud(s) supplémentaire(s) non affiché(s).`;
    listContainer.appendChild(infoItem);

    // Message dans la partie centrale (node-card)
    const notice = document.createElement('p');
    notice.className = 'empty-state';
    notice.style.marginTop = '1rem';
    notice.textContent = `${remaining} résultat(s) supplémentaire(s) non affiché(s).`;
    container.appendChild(notice);
  }

  Prism.highlightAll();
}


document.addEventListener('DOMContentLoaded', async () => {
  await loadJSON();

  const input = document.getElementById('node-search');

  const params = new URLSearchParams(window.location.search);
  const initialQuery = params.get('search');
  if (initialQuery) {
    input.value = initialQuery;
    triggerSearch(initialQuery);
  }

  function triggerSearch(q) {
    const matches = allNodes.filter(n =>
      n.name.toLowerCase().includes(q.toLowerCase()) ||
      n.description.toLowerCase().includes(q.toLowerCase())
    );
    renderResults(matches);
  }

  input.addEventListener('input', debounce(() => {
    const q = input.value.trim();
    if (q.length < 1) {
      document.getElementById('node-list').innerHTML = '';
      document.getElementById('nodes-container').innerHTML = `
        <div class="empty-state">
          <img src="../assets/images/sleep.gif" alt="Aucun nœud sélectionné"/>
          <p>Commencez votre recherche pour voir des nœuds</p>
        </div>`;
      return;
    }
    triggerSearch(q);
  }, 100));
});
