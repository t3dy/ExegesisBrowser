/**
 * PKD Exegesis Knowledge Portal - Core Logic
 * Prioritizes global JavaScript data to bypass local CORS restrictions.
 */

const state = {
    dictionary: window.EXEGESIS_DICTIONARY || [],
    analyticsData: window.EXEGESIS_ANALYTICS || null,
    graphData: window.EXEGESIS_GRAPH || null,
    sourceStructure: window.EXEGESIS_STRUCTURE || [],
    segmentSummaries: window.EXEGESIS_SUMMARIES || [],
    cy: null,
    charts: {}
};

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', async () => {
    // If globals are missing, try fetching as a fallback (for hosted environments)
    if (state.dictionary.length === 0) {
        console.log("Global data missing, attempting fetch fallback...");
        await loadDataFallback();
    }

    initUI();
    renderCards(state.dictionary);
});

async function loadDataFallback() {
    try {
        const [dictRes, graphRes, statsRes] = await Promise.all([
            fetch('assets/data/dictionary_expanded.json').then(r => r.json()).catch(() => []),
            fetch('assets/data/graph_data.json').then(r => r.json()).catch(() => null),
            fetch('assets/data/analytics_summary.json').then(r => r.json()).catch(() => null)
        ]);
        state.dictionary = dictRes;
        state.graphData = graphRes;
        state.analyticsData = statsRes;
    } catch (e) {
        console.error("Data fallback loading failed", e);
    }
}

function initUI() {
    const search = document.getElementById('term-search');
    if (search) {
        search.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            const filtered = state.dictionary.filter(item =>
                item.term.toLowerCase().includes(query) ||
                (item.definition && item.definition.toLowerCase().includes(query)) ||
                (item.technical_definition && item.technical_definition.toLowerCase().includes(query))
            );
            renderCards(filtered);
        });
    }

    // Populate Category Filter Bar
    const filterBar = document.getElementById('filter-bar');
    if (filterBar && state.dictionary.length > 0) {
        const categories = ['All', ...new Set(state.dictionary.map(item => item.category))];
        filterBar.innerHTML = categories.map(cat => `
            <span class="filter-tag ${cat === 'All' ? 'active' : ''}" data-category="${cat}">
                ${cat === 'All' ? 'All' : cat.split(' ')[0]}
            </span>
        `).join('');

        filterBar.querySelectorAll('.filter-tag').forEach(tag => {
            tag.addEventListener('click', () => {
                filterBar.querySelectorAll('.filter-tag').forEach(t => t.classList.remove('active'));
                tag.classList.add('active');
                const cat = tag.dataset.category;
                const filtered = cat === 'All' ? state.dictionary : state.dictionary.filter(item => item.category === cat);
                renderCards(filtered);
            });
        });
    }
}

function renderCards(entries) {
    const grid = document.getElementById('cards-grid');
    if (!grid) return;

    if (entries.length === 0) {
        grid.innerHTML = '<p class="no-results">No matching terms found in the Exegesis.</p>';
        return;
    }

    grid.innerHTML = entries.map(entry => {
        const slug = entry.term.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
        return `
            <div class="card" data-category="${entry.category}">
                <span class="category">${entry.category}</span>
                <h3>${entry.term}</h3>
                <p>${entry.technical_definition || (entry.definition ? entry.definition.substring(0, 100) + '...' : 'Entry in the PKD Exegesis network.')}</p>
                <a href="cards/${slug}.html" class="portal-btn">View Portal &rarr;</a>
            </div>
        `;
    }).join('');
}

window.switchTab = function (tab) {
    console.log(`Switching to tab: ${tab}`);
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('onclick')?.includes(`'${tab}'`)) {
            btn.classList.add('active');
        }
    });

    // Toggle views
    const views = ['cards', 'analytics', 'graph', 'source'];
    views.forEach(v => {
        const el = document.getElementById(`${v}-view`);
        if (el) {
            el.classList.remove('view-active', 'view-hidden');
            el.classList.add(v === tab ? 'view-active' : 'view-hidden');
        }
    });

    // Initialize specific view logic
    if (tab === 'graph') {
        initGraph();
    } else if (tab === 'analytics') {
        initAnalytics();
    } else if (tab === 'source') {
        initSourceBrowser();
    }
};

function initSourceBrowser() {
    const list = document.getElementById('segment-list');
    if (!list || list.children.length > 0) return;

    list.innerHTML = state.sourceStructure.map(seg => `
        <div class="segment-item" data-id="${seg.segment_id}">
            <span class="seg-type">${seg.type}</span>
            <span class="seg-val">${seg.value}</span>
        </div>
    `).join('');

    list.querySelectorAll('.segment-item').forEach(item => {
        item.addEventListener('click', () => {
            list.querySelectorAll('.segment-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            renderSegmentDetail(item.dataset.id);
        });
    });
}

function renderSegmentDetail(segId) {
    const detail = document.getElementById('segment-detail');
    const placeholder = document.getElementById('segment-detail-placeholder');
    const summary = state.segmentSummaries.find(s => s.segment_id === segId);

    if (!summary) return;

    placeholder.classList.add('view-hidden');
    detail.classList.remove('view-hidden');

    document.getElementById('seg-title').textContent = summary.title;
    document.getElementById('seg-summary').textContent = summary.summary_200_400_words;

    document.getElementById('seg-theses').innerHTML = summary.core_theses.map(t => `<li>${t}</li>`).join('');
    document.getElementById('seg-peaks').innerHTML = (summary.visionary_peaks || []).map(p => `<li>${p}</li>`).join('');

    const anchors = document.getElementById('seg-anchors');
    anchors.innerHTML = summary.evidence_anchors.map(a => `
        <div class="anchor-box">
            <p>"${a}"</p>
        </div>
    `).join('');
}

// --- ANALYTICS LOGIC ---
function initAnalytics() {
    console.log("Initializing Analytics Dashboard...");
    if (!state.analyticsData) return;

    const configs = [
        { id: 'chart-top-terms', type: 'bar', data: state.analyticsData.top_overall, title: 'Mentions' },
        { id: 'chart-categories', type: 'doughnut', data: state.analyticsData.category_distribution, title: 'Terms' },
        { id: 'chart-figures', type: 'bar', data: state.analyticsData.top_figures, title: 'Mentions' },
        { id: 'chart-themes', type: 'bar', data: state.analyticsData.top_themes, title: 'Mentions' }
    ];

    Object.values(state.charts).forEach(c => c.destroy());
    state.charts = {};

    setTimeout(() => {
        configs.forEach(conf => {
            const canvas = document.getElementById(conf.id);
            if (!canvas) return;

            const ctx = canvas.getContext('2d');
            try {
                state.charts[conf.id] = new Chart(ctx, {
                    type: conf.type,
                    data: {
                        labels: Object.keys(conf.data || {}),
                        datasets: [{
                            label: conf.title,
                            data: Object.values(conf.data || {}),
                            backgroundColor: conf.type === 'bar' ? 'rgba(255, 204, 0, 0.6)' :
                                ['#ffcc00', '#ff6600', '#00ffcc', '#cc00ff', '#3399ff', '#66ff66'],
                            borderColor: '#1a1a1a',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: conf.type !== 'bar',
                                position: 'bottom',
                                labels: { color: '#e0e0e0' }
                            }
                        },
                        scales: conf.type === 'bar' ? {
                            y: { beginAtZero: true, ticks: { color: '#888' } },
                            x: { ticks: { color: '#888', font: { size: 10 } } }
                        } : {}
                    }
                });
            } catch (err) {
                console.error(`Error rendering ${conf.id}:`, err);
            }
        });
    }, 100);
}

// --- GRAPH LOGIC ---
function initGraph() {
    if (state.cy || !state.graphData) return;

    const container = document.getElementById('cy');
    if (!container) return;

    state.cy = cytoscape({
        container: container,
        elements: state.graphData,
        style: [
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'color': '#fff',
                    'font-size': '8px',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'background-color': '#3b82f6',
                    'width': '20px',
                    'height': '20px',
                    'text-outline-width': 1,
                    'text-outline-color': '#1a1a1a'
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
                    'line-color': '#4b5563',
                    'curve-style': 'haystack',
                    'opacity': 0.2
                }
            }
        ],
        layout: {
            name: 'cose',
            animate: false
        }
    });

    state.cy.on('tap', 'node', (evt) => {
        const data = evt.target.data();
        const panel = document.getElementById('node-info');
        const content = document.getElementById('node-info-content');

        if (!panel || !content) return;

        let html = `<h3>${data.label}</h3>`;
        if (data.type === 'term') {
            html += `<p class="meta">Category: ${data.category}</p>`;
            html += `<p>Mention Count: ${data.count || 'N/A'}</p>`;
        } else {
            html += `<div class="passage-text">"${data.text}"</div>`;
            html += `<p class="meta">Source Range: Lines ${data.lines}</p>`;
            if (data.terms && data.terms.length) {
                html += `<h4>Connected Concepts:</h4><div class="term-tags">`;
                data.terms.forEach(t => html += `<span class="tag">${t}</span>`);
                html += `</div>`;
            }
        }

        content.innerHTML = html;
        panel.classList.remove('view-hidden');
    });
}
