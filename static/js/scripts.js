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
    const comparisonSection = document.querySelector('#comparison');
    if (comparisonSection) {
        comparisonSection.scrollIntoView({ behavior: 'smooth' });
    }
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
    const vVeiculos = Number(document.getElementById('valor-veiculos')?.value) || 0;
    const vImoveis = Number(document.getElementById('valor-imoveis')?.value) || 0;
    const vDinheiro = Number(document.getElementById('valor-dinheiro')?.value) || 0;
    return { veiculos: vVeiculos, imoveis: vImoveis, dinheiro: vDinheiro };
}

function calculateSavings(assets) {
    const years = 20;
    const savings = [];

    for (let y = 0; y <= years; y++) {
        let totalSavings = 0;
        const veiculosWithout = assets.veiculos * (0.025 * y + (y >= 10 ? 0.15 : 0) + (y == 20 ? 0.15 : 0));
        const veiculosWith = assets.veiculos * (0.01 * y);
        totalSavings += veiculosWithout - veiculosWith;
        const imoveisWithout = assets.imoveis * (0.01 * y + (y >= 10 ? 0.15 + 0.08 : 0) + (y == 20 ? 0.15 + 0.08 : 0));
        const imoveisWith = assets.imoveis * (0.005 * y);
        totalSavings += imoveisWithout - imoveisWith;
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
    if (comparisonChart) {
        comparisonChart.data.datasets[0].data = savings;
        comparisonChart.update();
    }
}

// Comparison Section Logic
const models = {
    aluguel: {
        blocks: [
            { highlight: 'Mais de 8% de Economia', text: 'nos impostos sobre aluguéis, otimizando seus ganhos com a W1 Holding.' },
            { highlight: 'Até R$2.400 Anuais', text: 'de redução tributária para aluguéis de R$30.000, aumentando sua rentabilidade.' }
        ],
        image: window.modelImages?.aluguel || '',
        text: 'A W1 Holding reduz a tributação de aluguéis de 27,5% para até 11%, economizando até R$2.400 por ano em um aluguel de R$30.000, com segurança e eficiência.'
    },
    empresas: {
        blocks: [
            { highlight: 'Até 27,5% de Isenção', text: 'em impostos na distribuição de lucros, maximizando seus retornos.' },
            { highlight: 'Mais de R$27.500', text: 'de economia anual em lucros de R$100.000 com a W1 Holding.' }
        ],
        image: window.modelImages?.empresas || '',
        text: 'Com a W1 Holding, distribua lucros com isenção de até 27,5% de impostos, economizando até R$27.500 anuais em lucros de R$100.000, com total conformidade fiscal.'
    },
    sucessorio: {
        blocks: [
            { highlight: 'Até 36 Meses a Menos', text: 'em processos de inventário, garantindo agilidade e proteção.' },
            { highlight: 'Mais de R$150.000', text: 'de economia em custos sucessórios com a W1 Holding.' }
        ],
        image: window.modelImages?.sucessorio || '',
        text: 'A W1 Holding simplifica a sucessão patrimonial, reduzindo o tempo de inventário em até 36 meses e eliminando custos de até R$150.000, assegurando tranquilidade para sua família.'
    }
};

let currentModel = 'aluguel';
let timerInterval;
const timerDuration = 5000;

function updateModel(model) {
    const data = models[model];
    const block1 = document.getElementById('block1');
    const block2 = document.getElementById('block2');
    const modelImage = document.getElementById('model-image');
    const modelText = document.getElementById('model-text');

    if (!block1 || !block2 || !modelImage || !modelText) {
        console.error('Comparison section elements missing');
        return;
    }

    // Reset animations
    const textElements = document.querySelectorAll('.savings-number, .savings-text, .image-text');
    textElements.forEach(el => {
        el.classList.remove('slide-in');
    });

    // Update content
    block1.innerHTML = `<div class="savings-number">${data.blocks[0].highlight}</div><p class="savings-text">${data.blocks[0].text}</p>`;
    block2.innerHTML = `<div class="savings-number">${data.blocks[1].highlight}</div><p class="savings-text">${data.blocks[1].text}</p>`;
    modelImage.src = data.image;
    modelText.textContent = data.text;

    // Apply slide-in animation
    setTimeout(() => {
        textElements.forEach(el => {
            el.classList.add('slide-in');
        });
    }, 0);

    document.querySelectorAll('.model-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.model === model) btn.classList.add('active');
    });
    document.querySelectorAll('.timer-line').forEach(line => {
        line.classList.remove('active');
        line.style.width = '0';
        if (line.dataset.model === model) line.classList.add('active');
    });
    currentModel = model;
    resetTimer();
}

function startTimer() {
    const activeTimerLine = document.querySelector('.timer-line.active');
    if (activeTimerLine) activeTimerLine.style.width = '100%';
    timerInterval = setTimeout(() => {
        const modelsList = Object.keys(models);
        const currentIndex = modelsList.indexOf(currentModel);
        const nextModel = modelsList[(currentIndex + 1) % modelsList.length];
        updateModel(nextModel);
    }, timerDuration);
}

function resetTimer() {
    clearTimeout(timerInterval);
    document.querySelectorAll('.timer-line').forEach(line => {
        line.style.width = '0';
        if (line.classList.contains('active')) line.style.width = '100%';
    });
    startTimer();
}

function stopTimer() {
    clearTimeout(timerInterval);
    const activeTimerLine = document.querySelector('.timer-line.active');
    if (activeTimerLine) activeTimerLine.style.width = activeTimerLine.style.width;
}

function initializeComparison() {
    const imageContainer = document.getElementById('image-container');
    if (!imageContainer) {
        console.error('Image container not found');
        return;
    }

    document.querySelectorAll('.model-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            updateModel(btn.dataset.model);
        });
    });

    imageContainer.addEventListener('mouseenter', stopTimer);
    imageContainer.addEventListener('mouseleave', resetTimer);

    updateModel('aluguel');
}

// Steps Animations
document.addEventListener('DOMContentLoaded', () => {
    console.log('scripts.js loaded');

    // Chart
    initializeChart();
    updateChart();

    // Steps Animations
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

    // Comparison
    initializeComparison();
});