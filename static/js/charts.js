// Initialize all charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get chart data from data attributes
    const monthlyTrendsData = JSON.parse(document.getElementById('chart-data').dataset.monthly);
    const incomeData = JSON.parse(document.getElementById('chart-data').dataset.income);
    const expensesData = JSON.parse(document.getElementById('chart-data').dataset.expenses);
    
    // Create charts
    createMonthlyTrendsChart(monthlyTrendsData);
    createIncomeChart(incomeData);
    createExpensesChart(expensesData);
});

function createMonthlyTrendsChart(data) {
    new Chart(
        document.getElementById('monthlyTrendsChart'),
        {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'Income',
                        data: data.income,
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        tension: 0.1,
                        fill: true
                    },
                    {
                        label: 'Expenses',
                        data: data.expenses,
                        borderColor: '#F44336',
                        backgroundColor: 'rgba(244, 67, 54, 0.1)',
                        tension: 0.1,
                        fill: true
                    }
                ]
            },
            options: getCommonOptions('$')
        }
    );
}

function createIncomeChart(data) {
    new Chart(
        document.getElementById('incomeChart'),
        {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: [
                        '#4CAF50', '#8BC34A', '#CDDC39', '#FFEB3B',
                        '#FFC107', '#FF9800', '#FF5722'
                    ],
                    borderWidth: 1
                }]
            },
            options: getCommonOptions('$')
        }
    );
}

function createExpensesChart(data) {
    new Chart(
        document.getElementById('expensesChart'),
        {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: [
                        '#F44336', '#E91E63', '#9C27B0', '#673AB7',
                        '#3F51B5', '#2196F3', '#03A9F4'
                    ],
                    borderWidth: 1
                }]
            },
            options: getCommonOptions('$')
        }
    );
}

// Common chart options
function getCommonOptions(currencySymbol) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return `${context.dataset.label || context.label}: ${currencySymbol}${context.raw.toFixed(2)}`;
                    }
                }
            },
            legend: {
                position: 'bottom',
                labels: {
                    boxWidth: 12,
                    padding: 20
                }
            }
        }
    };
}