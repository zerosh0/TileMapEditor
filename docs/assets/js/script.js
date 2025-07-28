document.addEventListener("DOMContentLoaded", () => {
  const headings = Array.from(document.querySelectorAll(".content .inner h1[id], .content .inner h2[id], .content .inner h3[id]"));
  const tocLinks = Array.from(document.querySelectorAll(".sidebar-right .toc a"));


  // Fonction qui met à jour l'item actif en parcourant les titres
  function updateActiveLink() {
    let currentId = headings[0].id;
    for (const h of headings) {
      // 80px = hauteur du header + marge, ajuste si besoin
      if (h.getBoundingClientRect().top <= 205) {
        currentId = h.id;
      } else {
        break;
      }
    }
    tocLinks.forEach(a => a.classList.toggle("active", a.getAttribute("href").slice(1) === currentId));
  }

  // Throttle basique pour alléger les appels
  let ticking = false;
  window.addEventListener("scroll", () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        updateActiveLink();
        ticking = false;
      });
      ticking = true;
    }
  });

  // Initialiser tout de suite
  updateActiveLink();
});

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("mobile-menu-btn");
  const sidebar = document.querySelector(".sidebar-left");

  btn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
  });

  // Optionnel : cliquer hors de la sidebar la referme
  document.addEventListener("click", (e) => {
    if (
      sidebar.classList.contains("open") &&
      !sidebar.contains(e.target) &&
      e.target !== btn
    ) {
      sidebar.classList.remove("open");
    }
  });
});




document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('.sidebar-left .toggle-icon').forEach(icon => {
    const li = icon.closest('li.has-sub');
    const submenu = li.querySelector('.submenu');
    const chevron = icon.querySelector('i');

    icon.addEventListener('click', e => {
      e.stopPropagation();

      if (li.classList.contains('open')) {
        submenu.style.maxHeight = '0px';
        li.classList.remove('open');
        chevron.classList.replace('fa-chevron-up', 'fa-chevron-down');
      } else {
        li.classList.add('open');
        chevron.classList.replace('fa-chevron-down', 'fa-chevron-up');
        submenu.style.maxHeight = submenu.scrollHeight + 'px';
      }
    });

    if (li.classList.contains('open')) {
      submenu.style.maxHeight = submenu.scrollHeight + 'px';
    }
  });
});
document.querySelector('.sidebar-left .menu-item a.active')?.closest('li.has-sub')?.classList.add('open');


document.addEventListener("DOMContentLoaded", () => {
  // 1) on commence par traiter les <picture>
  document.querySelectorAll('.content picture:not(.no-bg)').forEach(picture => {
    wrapWithBlur(picture);
  });

  // 2) puis les <img> libres, sans bg-blur ni déjà enveloppés
  document.querySelectorAll('.content img:not(.no-bg):not(.bg-blur)').forEach(img => {
    if (!img.closest('picture')) {
      wrapWithBlur(img);
    }
  });
});

function wrapWithBlur(node) {
  // si c'est déjà dans un wrapper, on sort
  if (node.closest('.image-wrapper')) return;

  // crée le wrapper
  const wrapper = document.createElement('div');
  wrapper.className = 'image-wrapper';

  // crée l'image floutée de fond
  const blurImg = document.createElement('img');
  blurImg.classList.add('bg-blur');
  const assetPath = window.location.pathname.includes('index.html') ? 'assets/' : '../assets/';
  blurImg.src = `${assetPath}images/bg.jpg`;


  // insère le wrapper avant le nœud cible
  node.parentNode.insertBefore(wrapper, node);
  // puis ajoute le flou et le nœud (img ou picture) à l’intérieur
  wrapper.appendChild(blurImg);
  wrapper.appendChild(node);
}
document.addEventListener('DOMContentLoaded', async () => {
  // 1. Charger l'index JSON
  const assetPath = window.location.pathname.includes('index.html') ? 'assets/' : '../assets/';
  const res = await fetch(`${assetPath}search_index.json`);
  const docs = await res.json();

  // 2. Initialiser Fuse.js
  const fuse = new Fuse(docs, {
    keys: ['title', 'content'],
    threshold: 0.3,      // plus strict quand plus bas
    includeScore: true,
    ignoreLocation: true
  });

  // 3. Références DOM
  const input = document.getElementById('search');
  const resultsContainer = document.getElementById('search-results');

  // 4. Réagir à la frappe
  input.addEventListener('input', () => {
    const q = input.value.trim();
    if (q.length < 1) {
      resultsContainer.classList.remove('visible');
      return;
    }

    const results = fuse.search(q, { limit: 10 });

    // 5. Afficher les résultats
    resultsContainer.innerHTML = '';
    results.forEach(({ item }) => {
      const a = document.createElement('a');
      if (window.location.pathname === "/" || window.location.pathname.includes("index.html")) {
        a.href = `./pages/${item.url}`;
      } else {
        a.href = item.url;
      }

      a.textContent = item.title;
      resultsContainer.appendChild(a);
    });


    // 6. Afficher ou masquer le container
    if (results.length) {
      resultsContainer.classList.add('visible');
    } else {
      resultsContainer.classList.remove('visible');
    }
  });

  // 7. Fermer si on clique en dehors
  document.addEventListener('click', e => {
    const container = document.getElementById('search-container');
    if (!container.contains(e.target)) {
      resultsContainer.classList.remove('visible');
    }
  });
});
