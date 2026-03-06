document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('entrySearch');
    const cards = document.querySelectorAll('.card');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const sections = {
        grid: document.getElementById('entryGrid'),
        graph: document.getElementById('cy-container')
    };
    const nodeInfo = document.getElementById('nodeInfo');
    const filterTags = document.querySelectorAll('.filter-tag');

    let cy = null;

    // --- TAB SWITCHING ---
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-tab');

            // Toggle active button
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Toggle sections
            Object.keys(sections).forEach(key => {
                const el = sections[key];
                if (el) {
                    el.style.display = key === target ? (key === 'grid' ? 'grid' : 'block') : 'none';
                }
            });

            if (target === 'graph' && !cy) {
                initGraph();
            }
        });
    });

    // --- SEARCH LOGIC ---
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            cards.forEach(card => {
                const title = card.getAttribute('data-title').toLowerCase();
                const text = card.querySelector('p').textContent.toLowerCase();
                card.style.display = (title.includes(query) || text.includes(query)) ? 'flex' : 'none';
            });
        });
    }

    // --- FILTERING LOGIC ---
    filterTags.forEach(tag => {
        tag.addEventListener('click', () => {
            const category = tag.getAttribute('data-category');

            filterTags.forEach(t => t.classList.remove('active'));
            tag.classList.add('active');

            cards.forEach(card => {
                const cardCat = card.getAttribute('data-category');
                if (category === 'all' || cardCat === category) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    });

    // --- CYTOSCAPE GRAPH ---
    async function initGraph() {
        try {
            const response = await fetch('assets/data/graph_data.json');
            const elements = await response.json();

            cy = cytoscape({
                container: document.getElementById('cy'),
                elements: elements,
                style: [
                    {
                        selector: 'node',
                        style: {
                            'label': 'data(label)',
                            'color': '#fff',
                            'font-size': '10px',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'background-color': '#3b82f6',
                            'width': '20px',
                            'height': '20px'
                        }
                    },
                    {
                        selector: 'node[type="passage"]',
                        style: {
                            'background-color': '#10b981',
                            'shape': 'round-rectangle',
                            'width': '15px',
                            'height': '15px'
                        }
                    },
                    {
                        selector: 'edge',
                        style: {
                            'width': 1,
                            'line-color': '#1f2937',
                            'curve-style': 'bezier',
                            'opacity': 0.3
                        }
                    },
                    {
                        selector: 'edge[type="similarity"]',
                        style: {
                            'line-style': 'dashed',
                            'line-color': '#4b5563'
                        }
                    }
                ],
                layout: {
                    name: 'cose',
                    padding: 50,
                    nodeRepulsion: 4500,
                    animate: true
                }
            });

            cy.on('tap', 'node', function (evt) {
                const node = evt.target;
                const data = node.data();

                let infoHtml = `<h3>${data.label}</h3>`;
                if (data.type === 'term') {
                    infoHtml += `<p><strong>Category:</strong> ${data.category}</p>`;
                    infoHtml += `<p><strong>Mentions:</strong> ${data.count}</p>`;
                } else {
                    infoHtml += `<div class="passage-box"><p style="font-style: italic; color: #9ca3af;">"${data.text}"</p></div>`;
                    infoHtml += `<p><small>Lines: ${data.lines}</small></p>`;
                    infoHtml += `<h4 style="margin-top:1rem;">Linked Concepts:</h4><ul style="padding-left:1.5rem;">`;
                    if (data.terms) data.terms.forEach(t => infoHtml += `<li>${t}</li>`);
                    infoHtml += `</ul>`;
                }

                nodeInfo.innerHTML = infoHtml + `<button onclick="this.parentElement.style.display='none'" style="margin-top:1.5rem; width:100%; padding:0.5rem; background:#1f2937; color:white; border:1px solid #374151; border-radius:8px; cursor:pointer;">Close</button>`;
                nodeInfo.style.display = 'block';
            });

        } catch (err) {
            console.error("Error loading graph data:", err);
        }
    }
});
