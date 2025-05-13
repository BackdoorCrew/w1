function selectPlan(plan) {
    document.querySelectorAll('.plan-item').forEach(item => {
        item.classList.remove('active');
    });

    const selectedItem = document.querySelector(`.plan-item[data-plan="${plan}"]`);
    if (selectedItem) {
        selectedItem.classList.add('active');
    }

    console.log(`Plano ${plan} selecionado.`);
}

function comparePrices() {
    // Função existente ou placeholder
    console.log("Comparando preços...");
}

// Função para Google Sign-In
function handleCredentialResponse(response) {
    fetch('/accounts/google/login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ id_token: response.credential })
    })
    .then(response => {
        if (response.ok) {
            window.location.href = '/dashboard/';
        } else {
            console.error('Erro ao autenticar com Google');
        }
    })
    .catch(error => console.error('Erro:', error));
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Funções do gráfico
let comparisonChart;
const itemValues = {
    car: 100000,
    house: 1000000,
    cash: 500000
};
let quantities = {
    car: 0,
    house: 0,
    cash: 0
};

function initializeChart() {
    const ctx = document.getElementById('comparisonChart');
    if (!ctx) {
        console.error('Canvas #comparisonChart não encontrado');
        return;
    }
    comparisonChart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: Array.from({ length: 21 }, (_, i) => i),
            datasets: [
                {
                    label: 'Custos com Holding (R$)',
                    data: [],
                    borderColor: '#5fded4',
                    backgroundColor: 'rgba(95, 222, 212, 0.2)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Custos sem Holding (R$)',
                    data: [],
                    borderColor: '#ff6b6b',
                    backgroundColor: 'rgba(255, 107, 107, 0.2)',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                x: { 
                    title: { display: true, text: 'Anos', color: '#fff' },
                    ticks: { color: '#fff' }
                },
                y: { 
                    title: { display: true, text: 'Custo (R$)', color: '#fff' }, 
                    beginAtZero: true,
                    ticks: { color: '#fff' }
                }
            },
            plugins: {
                legend: { 
                    display: true,
                    position: 'top',
                    labels: { color: '#fff', font: { size: 14 } }
                }
            }
        }
    });
}

function calculateCosts(assetsValue) {
    const years = 20;
    const withHoldingCosts = [];
    const withoutHoldingCosts = [];

    for (let year = 0; year <= years; year++) {
        let withCost = year * assetsValue * 0.015;
        if (year % 10 === 0 && year > 0) {
            withCost += assetsValue * 0.02;
        }
        withHoldingCosts.push(withCost);

        let withoutCost = year * assetsValue * 0.03;
        if (year % 10 === 0 && year > 0) {
            withoutCost += assetsValue * 0.08;
        }
        withoutHoldingCosts.push(withoutCost);
    }

    return { withHoldingCosts, withoutHoldingCosts };
}

function updateChart() {
    const totalValue = 
        quantities.car * itemValues.car +
        quantities.house * itemValues.house +
        quantities.cash * itemValues.cash;

    const { withHoldingCosts, withoutHoldingCosts } = calculateCosts(totalValue);

    if (comparisonChart) {
        comparisonChart.data.datasets[0].data = withHoldingCosts;
        comparisonChart.data.datasets[1].data = withoutHoldingCosts;
        comparisonChart.update();
    }
}

function adjustQuantity(item, change) {
    if (quantities[item] + change < 0) return;
    quantities[item] += change;
    const quantityElement = document.getElementById(`${item}-quantity`);
    if (quantityElement) {
        quantityElement.textContent = quantities[item];
    }
    const btn = event.target;
    btn.classList.add('animate');
    setTimeout(() => btn.classList.remove('animate'), 300);
    updateChart();
}

document.addEventListener('DOMContentLoaded', () => {
    initializeChart();
    updateChart();
});

// Rolagem suave para links de navegação
document.querySelectorAll('.nav-links a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const targetId = this.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
            targetElement.scrollIntoView({ behavior: 'smooth' });
        }
    });
});