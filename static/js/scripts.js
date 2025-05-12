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

// Configuração inicial do gráfico
let comparisonChart;
const itemValues = {
    car: 100000,    // R$100.000 por carro
    house: 1000000, // R$1.000.000 por casa
    cash: 500000    // R$500.000 por unidade de dinheiro
};
let quantities = {
    car: 0,
    house: 0,
    cash: 0
};

function initializeChart() {
    const ctx = document.getElementById('comparisonChart').getContext('2d');
    comparisonChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({ length: 21 }, (_, i) => i), // 0 a 20 anos
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
                x: { title: { display: true, text: 'Anos', color: '#fff' } },
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
        // Com holding: 1.5% imposto anual + 2% sucessão a cada 10 anos
        let withCost = year * assetsValue * 0.015;
        if (year % 10 === 0 && year > 0) {
            withCost += assetsValue * 0.02;
        }
        withHoldingCosts.push(withCost);

        // Sem holding: 3% imposto anual + 8% sucessão a cada 10 anos
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

    comparisonChart.data.datasets[0].data = withHoldingCosts;
    comparisonChart.data.datasets[1].data = withoutHoldingCosts;
    comparisonChart.update();
}

function adjustQuantity(item, change) {
    // Impedir quantidade negativa
    if (quantities[item] + change < 0) return;

    // Atualizar quantidade
    quantities[item] += change;
    document.getElementById(`${item}-quantity`).textContent = quantities[item];

    // Adicionar animação ao botão
    const btn = event.target;
    btn.classList.add('animate');
    setTimeout(() => btn.classList.remove('animate'), 300);

    // Atualizar gráfico
    updateChart();
}

// Inicializar gráfico ao carregar a página
document.addEventListener('DOMContentLoaded', () => {
    initializeChart();
    updateChart(); // Renderizar com valores iniciais (0)
});