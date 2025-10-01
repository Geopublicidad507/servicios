// Financial Chart
function initFinancialChart() {
    const ctx = document.getElementById('financialChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
            datasets: [{
                label: 'Ingresos',
                data: [12000, 15000, 13500, 16000, 14500, 17000, 15500, 18000, 16500, 19000, 17500, 20000],
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            }, {
                label: 'Gastos',
                data: [8000, 9500, 8800, 10200, 9100, 11000, 9800, 12000, 10500, 13000, 11500, 14000],
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Properties Chart
function initPropertiesChart() {
    const ctx2 = document.getElementById('propertiesChart').getContext('2d');
    new Chart(ctx2, {
        type: 'doughnut',
        data: {
            labels: ['Activas', 'Al Día', 'Con Atrasos'],
            datasets: [{
                data: [5, 4, 1],
                backgroundColor: ['#0d6efd', '#198754', '#ffc107'],
                hoverBackgroundColor: ['#0b5ed7', '#157347', '#ffca2c'],
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 1,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function refreshDashboard() {
    location.reload();
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = '/auth/login';
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initFinancialChart();
    initPropertiesChart();
});