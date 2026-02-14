const API_URL = ""; // Relative path for production


// Navigation
function showSection(sectionId) {
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active', 'hidden'));
    document.getElementById(sectionId).classList.add('active');

    document.querySelectorAll('.nav-links li').forEach(l => l.classList.remove('active'));
    // Simple active state toggle might need more logic based on click target text/id
}

// Investment Plan Logic
document.getElementById('investment-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const age = parseInt(document.getElementById('age').value);
    const income = parseFloat(document.getElementById('income').value);
    const goal = document.getElementById('goal').value;

    // Call API (Mocked for now until backend run)
    try {
        const response = await fetch(`${API_URL}/api/recommendation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                age, income, goal,
                profession: "Employee", // Default
                region: "India", // Default
                api_key: "" // Would need input
            })
        });

        const data = await response.json();

        // Show Results
        document.getElementById('plan-result').classList.remove('hidden');
        document.getElementById('advice-text').innerText = data.advice_text;

        renderChart(data.allocation);

    } catch (err) {
        alert("Error connecting to backend advisor.");
        console.error(err);
    }
});

let myChart = null;

function renderChart(allocation) {
    const ctx = document.getElementById('allocationChart').getContext('2d');

    // Parse values like "₹60,000" to numbers
    const labels = Object.keys(allocation);
    const data = Object.values(allocation).map(v => {
        if (typeof v === 'string') return parseInt(v.replace(/[^\d]/g, ''));
        return v;
    });

    if (myChart) myChart.destroy();

    myChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: ['#00d4ff', '#ff007a', '#ffd700'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom', labels: { color: 'white' } }
            }
        }
    });
}

// Mutual Fund Search
async function searchFunds() {
    const query = document.getElementById('fund-search').value;
    if (!query) return;

    try {
        const res = await fetch(`${API_URL}/api/funds/search?q=${query}`);
        const data = await res.json();

        const container = document.getElementById('fund-results');
        container.innerHTML = "";

        if (data.length === 0) {
            container.innerHTML = "<p>No funds found.</p>";
            return;
        }

        data.slice(0, 5).forEach(fund => {
            const div = document.createElement('div');
            div.className = "fund-item glass";
            div.style.marginTop = "10px";
            div.innerHTML = `<strong>${fund.schemeName}</strong><br><small>Code: ${fund.schemeCode}</small>`;
            container.appendChild(div);
        });
    } catch (err) {
        console.error("Fund search failed:", err);
    }
}

// Market Trends
let marketChart = null;
async function loadMarketData() {
    const symbol = document.getElementById('market-symbol').value;
    try {
        const res = await fetch(`${API_URL}/api/market/history?symbol=${symbol}`);
        const data = await res.json();

        if (!data || data.length === 0) return;

        const ctx = document.getElementById('marketChart').getContext('2d');
        if (marketChart) marketChart.destroy();

        marketChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: `${symbol} Price`,
                    data: data.map(d => d.close),
                    borderColor: '#00d4ff',
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                interaction: { intersect: false, mode: 'index' },
                scales: {
                    x: { ticks: { color: 'white' } },
                    y: { ticks: { color: 'white' } }
                },
                plugins: { legend: { labels: { color: 'white' } } }
            }
        });
    } catch (err) {
        console.error("Market data failed:", err);
    }
}

// Financial News
async function loadNews() {
    try {
        // Warning: Requires SERVER to have API Key set
        const res = await fetch(`${API_URL}/api/news?q=finance`);
        const articles = await res.json();

        const container = document.getElementById('news-container');
        container.innerHTML = "";

        if (articles.length === 0) {
            container.innerHTML = "<p>No news available (Check API Key).</p>";
            return;
        }

        articles.forEach(article => {
            const div = document.createElement('div');
            div.className = "news-item glass";
            div.style.marginTop = "15px";
            div.innerHTML = `
                <h4><a href="${article.url}" target="_blank" style="color:#00d4ff;text-decoration:none;">${article.title}</a></h4>
                <p><small>${new Date(article.publishedAt).toDateString()} | ${article.source.name}</small></p>
                <p>${article.description || ''}</p>
            `;
            container.appendChild(div);
        });
    } catch (err) {
        console.error("News failed:", err);
    }
}

// Economic Data
let economicChart = null;
async function loadEconomicData() {
    const seriesId = document.getElementById('fred-series').value;
    try {
        const res = await fetch(`${API_URL}/api/economic/data?series_id=${seriesId}`);
        const data = await res.json();

        const ctx = document.getElementById('economicChart').getContext('2d');
        if (economicChart) economicChart.destroy();

        economicChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: seriesId,
                    data: data.map(d => d.value),
                    backgroundColor: '#ffd700'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: { ticks: { color: 'white' } },
                    y: { ticks: { color: 'white' } }
                },
                plugins: { legend: { labels: { color: 'white' } } }
            }
        });
    } catch (err) {
        console.error("Economic data failed:", err);
    }
}
