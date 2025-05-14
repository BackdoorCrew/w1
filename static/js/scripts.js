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
    document.querySelector('#comparison').scrollIntoView({ behavior: 'smooth' });
}

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

let comparisonChart;

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
            datasets: [{
                label: 'Economia com Holding (R$)',
                data: [],
                borderColor: '#5fded4',
                backgroundColor: 'rgba(95, 222, 212, 0.2)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { 
                    title: { display: true, text: 'Anos', color: '#fff' },
                    ticks: { color: '#fff' }
                },
                y: { 
                    title: { display: true, text: 'Economia (R$)', color: '#fff' }, 
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

function getAssetsValue() {
    const vVeiculos = Number(document.getElementById('valor-veiculos').value) || 0;
    const vImoveis = Number(document.getElementById('valor-imoveis').value) || 0;
    const vDinheiro = Number(document.getElementById('valor-dinheiro').value) || 0;
    return { veiculos: vVeiculos, imoveis: vImoveis, dinheiro: vDinheiro };
}

function calculateSavings(assets) {
    const years = 20;
    const savings = [];

    for (let y = 0; y <= years; y++) {
        let totalSavings = 0;

        // Veículos: 2.5% IPVA + 15% capital gains every 10y (without); 1% effective (with)
        const veiculosWithout = assets.veiculos * (0.025 * y + (y >= 10 ? 0.15 : 0) + (y == 20 ? 0.15 : 0));
        const veiculosWith = assets.veiculos * (0.01 * y);
        totalSavings += veiculosWithout - veiculosWith;

        // Imóveis: 1% IPTU + 15% gains + 8% ITCMD every 10y (without); 0.5% effective (with)
        const imoveisWithout = assets.imoveis * (0.01 * y + (y >= 10 ? 0.15 + 0.08 : 0) + (y == 20 ? 0.15 + 0.08 : 0));
        const imoveisWith = assets.imoveis * (0.005 * y);
        totalSavings += imoveisWithout - imoveisWith;

        // Dinheiro: 20% on 5% annual return (without); 10% effective (with)
        const returnRate = 0.05;
        const dinheiroWithout = assets.dinheiro * returnRate * y * 0.20;
        const dinheiroWith = assets.dinheiro * returnRate * y * 0.10;
        totalSavings += dinheiroWithout - dinheiroWith;

        savings.push(totalSavings);
    }

    return savings;
}

function updateChart() {
    const assets = getAssetsValue();
    const savings = calculateSavings(assets);
    comparisonChart.data.datasets[0].data = savings;
    comparisonChart.update();
}

document.addEventListener('DOMContentLoaded', () => {
    initializeChart();
    updateChart();

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

    const stepsRows = document.querySelectorAll('.steps-row');
    if (stepsRows.length === 0) {
        console.error('Steps rows not found');
        return;
    }

    function getAbsoluteTop(element) {
        let top = 0;
        do {
            top += element.offsetTop || 0;
            element = element.offsetParent;
        } while (element);
        return top;
    }

    function updateTimelineLines() {
        const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
        const viewportHeight = window.innerHeight;
        const delayVh = 20;
        const delayPx = viewportHeight * (delayVh / 100);

        stepsRows.forEach(row => {
            const rowTop = getAbsoluteTop(row);
            const rowHeight = row.offsetHeight;
            let progress = (scrollPosition + viewportHeight - (rowTop + delayPx)) / rowHeight;
            progress = Math.min(Math.max(progress, 0), 1);
            const line = row.querySelector('.timeline-line');
            if (line) {
                line.style.width = `${progress * 100}%`;
            }

            const steps = row.querySelectorAll('.step');
            steps.forEach((step, index) => {
                const threshold = index / (steps.length - 1) || 0;
                if (progress >= threshold) {
                    step.classList.add('active');
                } else {
                    step.classList.remove('active');
                }
            });
        });
    }

    window.addEventListener('scroll', updateTimelineLines);
    window.addEventListener('load', updateTimelineLines);
});