// static/js/charts.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all charts
    initIncomeExpenseChart();
    initNetBalanceChart();
    initExpenseCategoryChart();
    initAssetsGrowthChart();
    initFinancialHealthChart();
    initCashFlowForecast();
    initTimeframeSelectors();
});

// 1. Income vs Expenses Chart
function initIncomeExpenseChart() {
    const ctx = document.getElementById('incomeExpenseCanvas');
    if (!ctx) {
        console.error('Income/Expense canvas not found');
        return;
    }

    const transactions = window.transactionData || [];
    console.log('Processing income/expense data:', transactions.length, 'transactions');

    const monthlyData = {};
    
    transactions.forEach(tx => {
        const txType = tx.transaction_type || tx.type;
        if (!['income', 'expense'].includes(txType)) return;
        
        try {
            const date = new Date(tx.date);
            const monthYear = date.toLocaleDateString('en-US', { 
                month: 'short', 
                year: 'numeric' 
            });
            
            if (!monthlyData[monthYear]) {
                monthlyData[monthYear] = { income: 0, expense: 0 };
            }
            
            const amount = Math.abs(Number(tx.amount));
            if (isNaN(amount)) {
                console.warn('Invalid amount for transaction:', tx);
                return;
            }
            
            monthlyData[monthYear][txType] += amount;
        } catch (e) {
            console.error('Error processing transaction:', tx, e);
        }
    });

    const sortedLabels = Object.keys(monthlyData).sort((a, b) => new Date(a) - new Date(b));
    console.log('Processed monthly data:', monthlyData);

    try {
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedLabels,
                datasets: [
                    {
                        label: 'Income',
                        data: sortedLabels.map(label => monthlyData[label].income),
                        backgroundColor: '#0EA5E9',
                        borderColor: '#0EA5E9',
                        borderRadius: 4,
                        borderWidth: 1
                    },
                    {
                        label: 'Expenses',
                        data: sortedLabels.map(label => monthlyData[label].expense),
                        backgroundColor: '#F43F5E',
                        borderColor: '#F43F5E',
                        borderRadius: 4,
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0, 0, 0, 0.1)' },
                        ticks: {
                            callback: value => '$' + value.toLocaleString()
                        }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: context => {
                                return `${context.dataset.label}: $${context.raw.toLocaleString()}`;
                            }
                        }
                    }
                }
            }
        });
        console.log('Income vs Expenses chart initialized');
    } catch (error) {
        console.error('Failed to create income/expense chart:', error);
        ctx.parentElement.innerHTML = '<div class="chart-error">Error loading chart</div>';
    }
}

// 2. Net Balance Trend Chart
function initNetBalanceChart() {
    const ctx = document.getElementById('netBalanceCanvas');
    if (!ctx) {
        console.error('Net Balance canvas not found');
        return;
    }

    const transactions = window.transactionData || [];
    console.log('Processing net balance data:', transactions.length, 'transactions');

    const monthlyNet = {};
    let runningBalance = 0;
    
    transactions
        .sort((a, b) => new Date(a.date) - new Date(b.date))
        .forEach(tx => {
            const txType = tx.transaction_type || tx.type;
            try {
                const date = new Date(tx.date);
                const monthYear = date.toLocaleDateString('en-US', { 
                    month: 'short', 
                    year: 'numeric' 
                });
                
                const amount = txType === 'income' 
                    ? Number(tx.amount) 
                    : -Math.abs(Number(tx.amount));
                
                if (isNaN(amount)) {
                    console.warn('Invalid amount for transaction:', tx);
                    return;
                }
                
                runningBalance += amount;
                monthlyNet[monthYear] = runningBalance;
            } catch (e) {
                console.error('Error processing transaction:', tx, e);
            }
        });

    const balanceLabels = Object.keys(monthlyNet);
    const balanceData = balanceLabels.map(label => monthlyNet[label]);
    console.log('Processed net balance data:', monthlyNet);

    try {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: balanceLabels,
                datasets: [{
                    label: 'Net Balance',
                    data: balanceData,
                    fill: true,
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    borderColor: '#10B981',
                    tension: 0.4,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: { color: 'rgba(0, 0, 0, 0.1)' },
                        ticks: {
                            callback: value => '$' + value.toLocaleString()
                        }
                    },
                    x: { 
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: context => {
                                return `Net Balance: $${context.raw.toLocaleString()}`;
                            }
                        }
                    }
                }
            }
        });
        console.log('Net Balance chart initialized');
    } catch (error) {
        console.error('Failed to create net balance chart:', error);
        ctx.parentElement.innerHTML = '<div class="chart-error">Error loading chart</div>';
    }
}

// 3. Expenses by Category Chart
function initExpenseCategoryChart() {
    const ctx = document.getElementById('expenseCategoryCanvas');
    if (!ctx) {
        console.error('Expense Category canvas not found');
        return;
    }

    const transactions = window.transactionData || [];
    console.log('Processing expense category data:', transactions.length, 'transactions');

    const categoryData = {};
    
    transactions.forEach(tx => {
        if ((tx.transaction_type || tx.type) !== 'expense') return;
        
        try {
            const category = tx.category || 'other';
            const amount = Math.abs(Number(tx.amount));
            
            if (isNaN(amount)) {
                console.warn('Invalid amount for transaction:', tx);
                return;
            }
            
            categoryData[category] = (categoryData[category] || 0) + amount;
        } catch (e) {
            console.error('Error processing transaction:', tx, e);
        }
    });

    const sortedCategories = Object.entries(categoryData)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    console.log('Processed expense categories:', categoryData);

    try {
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: sortedCategories.map(item => item[0]),
                datasets: [{
                    data: sortedCategories.map(item => item[1]),
                    backgroundColor: [
                        '#0EA5E9', '#F43F5E', '#10B981', '#8B5CF6', 
                        '#F59E0B', '#3B82F6', '#EC4899', '#14B8A6',
                        '#6366F1', '#EAB308'
                    ],
                    borderWidth: 1,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: context => {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const value = context.raw;
                                const percentage = Math.round((value / total) * 100);
                                return `${context.label}: $${value.toLocaleString()} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
        console.log('Expense Category chart initialized');
    } catch (error) {
        console.error('Failed to create expense category chart:', error);
        ctx.parentElement.innerHTML = '<div class="chart-error">Error loading chart</div>';
    }
}

// 4. Assets Growth Timeline
function initAssetsGrowthChart() {
    const ctx = document.getElementById('assetsCanvas');
    if (!ctx) return;

    // Verify data exists
    if (!window.transactionData || window.transactionData.length === 0) {
        ctx.parentElement.innerHTML = '<div class="chart-no-data">No asset data available</div>';
        return;
    }

    // Process asset transactions
    const assetsData = window.transactionData
        .filter(tx => (tx.transaction_type || tx.type) === 'assets')
        .map(tx => {
            return {
                x: tx.date,  // Keep as ISO string - Luxon will parse
                y: Math.abs(Number(tx.amount)),
                desc: tx.description || 'Asset'
            };
        })
        .filter(item => !isNaN(item.y));

    if (assetsData.length === 0) {
        ctx.parentElement.innerHTML = '<div class="chart-no-data">No valid asset transactions</div>';
        return;
    }

    // Calculate running total
    let runningTotal = 0;
    const points = assetsData.map(item => {
        runningTotal += item.y;
        return {
            x: item.x,
            y: runningTotal,
            desc: item.desc
        };
    });

    try {
        new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Total Assets',
                    data: points,
                    backgroundColor: 'rgba(139, 92, 246, 0.2)',
                    borderColor: '#8B5CF6',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'month',
                            tooltipFormat: 'MMM d, yyyy'
                        },
                        adapters: {
                            date: {
                                locale: 'en-US'
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: value => '$' + value.toLocaleString()
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: ctx => `Total: $${ctx.parsed.y.toLocaleString()}`,
                            afterLabel: ctx => ctx.raw.desc
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Assets chart error:', error);
        ctx.parentElement.innerHTML = `
            <div class="chart-error">
                <p>Technical issue loading chart</p>
                <small>${error.message}</small>
            </div>
        `;
    }
}

// 5. Financial Health Radar
function initFinancialHealthChart() {
    const ctx = document.getElementById('healthCanvas');
    if (!ctx) {
        console.error('Financial Health canvas not found');
        return;
    }

    const transactions = window.transactionData || [];
    console.log('Processing financial health data:', transactions.length, 'transactions');

    const now = new Date();
    const last30Days = new Date(now.setDate(now.getDate() - 30));
    
    const metrics = {
        'Savings Rate': calculateSavingsRate(transactions),
        'Liquidity': calculateLiquidity(transactions),
        'Debt Ratio': calculateDebtRatio(transactions),
        'Investment %': calculateInvestmentPercentage(transactions),
        'Expense Control': calculateExpenseControl(transactions, last30Days)
    };

    console.log('Calculated financial health metrics:', metrics);

    try {
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: Object.keys(metrics),
                datasets: [{
                    data: Object.values(metrics),
                    backgroundColor: 'rgba(99, 102, 241, 0.2)',
                    borderColor: '#6366F1',
                    pointBackgroundColor: '#6366F1',
                    pointHoverRadius: 6,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(0, 0, 0, 0.1)' },
                        suggestedMin: 0,
                        suggestedMax: 100,
                        ticks: { 
                            callback: value => value + '%',
                            backdropColor: 'transparent'
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: context => `${context.label}: ${context.raw}%`
                        }
                    }
                }
            }
        });
        console.log('Financial Health chart initialized');
    } catch (error) {
        console.error('Failed to create financial health chart:', error);
        ctx.parentElement.innerHTML = '<div class="chart-error">Error loading chart</div>';
    }
}

// 6. Cash Flow Forecast (Corrected Grouped Bars Version)
function initCashFlowForecast() {
    const ctx = document.getElementById('forecastCanvas');
    if (!ctx) {
        console.error('Cash Flow Forecast canvas not found');
        return;
    }

    const transactions = window.transactionData || [];
    console.log('Processing cash flow forecast data:', transactions.length, 'transactions');

    const recurring = transactions.filter(tx => 
        tx.frequency && tx.frequency !== 'one-time'
    );
    
    // Generate next 6 months labels
    const months = [...Array(6)].map((_, i) => {
        const date = new Date();
        date.setMonth(date.getMonth() + i);
        return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    });

    try {
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: months,
                datasets: [
                    {
                        label: 'Projected Income',
                        data: calculateProjected(recurring, 'income', months.length),
                        backgroundColor: 'rgba(16, 185, 129, 0.7)',
                        borderRadius: 4,
                        borderWidth: 1,
                        // These settings create grouped bars
                        categoryPercentage: 0.8,
                        barPercentage: 0.4
                    },
                    {
                        label: 'Projected Expenses',
                        data: calculateProjected(recurring, 'expense', months.length),
                        backgroundColor: 'rgba(239, 68, 68, 0.7)',
                        borderRadius: 4,
                        borderWidth: 1,
                        // Same grouping settings as income
                        categoryPercentage: 0.8,
                        barPercentage: 0.4
                    },
                    {
                        label: 'Projected Net',
                        data: calculateNetProjection(recurring, months.length),
                        type: 'line',
                        borderColor: '#3B82F6',
                        borderWidth: 3,
                        pointRadius: 5,
                        pointHoverRadius: 8,
                        pointBackgroundColor: '#3B82F6',
                        tension: 0.4,
                        fill: false,
                        // Make the line appear behind bars
                        order: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: { 
                            callback: value => '$' + value.toLocaleString() 
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: { 
                        grid: { display: false },
                        // Remove stacked property to enable side-by-side bars
                        stacked: false 
                    }
                },
                plugins: {
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: context => {
                                return `${context.dataset.label}: $${context.raw.toLocaleString()}`;
                            }
                        }
                    },
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    }
                },
                // Important for grouped bars
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
        console.log('Cash Flow Forecast chart initialized');
    } catch (error) {
        console.error('Failed to create cash flow forecast chart:', error);
        ctx.parentElement.innerHTML = '<div class="chart-error">Error loading chart</div>';
    }
}

// Helper Functions
function calculateSavingsRate(txs) {
    try {
        const income = txs
            .filter(tx => (tx.transaction_type || tx.type) === 'income')
            .reduce((sum, tx) => sum + Math.abs(Number(tx.amount)), 0);
        
        const expenses = txs
            .filter(tx => (tx.transaction_type || tx.type) === 'expense')
            .reduce((sum, tx) => sum + Math.abs(Number(tx.amount)), 0);
        
        return income > 0 ? Math.round(((income - expenses) / income) * 100) : 0;
    } catch (e) {
        console.error('Error calculating savings rate:', e);
        return 0;
    }
}

function calculateLiquidity(txs) {
    try {
        const liquidAssets = txs
            .filter(tx => (tx.transaction_type || tx.type) === 'assets' && 
                         ['cash', 'savings', 'checking'].includes(tx.category?.toLowerCase()))
            .reduce((sum, tx) => sum + Math.abs(Number(tx.amount)), 0);
        
        const monthlyExpenses = txs
            .filter(tx => (tx.transaction_type || tx.type) === 'expense')
            .reduce((sum, tx) => sum + Math.abs(Number(tx.amount)), 0) / 12;
        
        return monthlyExpenses > 0 ? Math.min(1000, Math.round((liquidAssets / monthlyExpenses) * 100)) : 1000;
    } catch (e) {
        console.error('Error calculating liquidity:', e);
        return 0;
    }
}

function calculateDebtRatio(txs) {
    try {
        const debts = txs
            .filter(tx => (tx.transaction_type || tx.type) === 'liability' || 
                         (tx.category?.toLowerCase() === 'debt'))
            .reduce((sum, tx) => sum + Math.abs(Number(tx.amount)), 0);
        
        const assets = txs
            .filter(tx => (tx.transaction_type || tx.type) === 'assets')
            .reduce((sum, tx) => sum + Math.abs(Number(tx.amount)), 1);
        
        return Math.min(100, Math.round((debts / assets) * 100));
    } catch (e) {
        console.error('Error calculating debt ratio:', e);
        return 0;
    }
}

function calculateInvestmentPercentage(txs) {
    try {
        const investments = txs
            .filter(tx => ['investment', 'stocks', 'bonds', 'real_estate']
                   .includes(tx.category?.toLowerCase()))
            .reduce((sum, tx) => sum + Math.abs(Number(tx.amount)), 0);
        
        const netWorth = calculateNetWorth(txs);
        
        return netWorth > 0 ? Math.round((investments / netWorth) * 100) : 0;
    } catch (e) {
        console.error('Error calculating investment percentage:', e);
        return 0;
    }
}

function calculateExpenseControl(txs, sinceDate) {
    try {
        const recentExpenses = txs
            .filter(tx => (tx.transaction_type || tx.type) === 'expense' && 
                         new Date(tx.date) >= sinceDate)
            .reduce((sum, tx) => sum + Math.abs(Number(tx.amount)), 0);
        
        const avgExpenses = txs
            .filter(tx => (tx.transaction_type || tx.type) === 'expense')
            .reduce((sum, tx) => sum + Math.abs(Number(tx.amount)), 0) / 12;
        
        return avgExpenses > 0 ? Math.max(0, 100 - Math.round((recentExpenses / avgExpenses) * 100)) : 100;
    } catch (e) {
        console.error('Error calculating expense control:', e);
        return 0;
    }
}

function calculateNetWorth(txs) {
    try {
        const assets = txs
            .filter(tx => (tx.transaction_type || tx.type) === 'assets')
            .reduce((sum, tx) => sum + Math.abs(Number(tx.amount)), 0);
        
        const liabilities = txs
            .filter(tx => (tx.transaction_type || tx.type) === 'liability')
            .reduce((sum, tx) => sum + Math.abs(Number(tx.amount)), 0);
        
        return assets - liabilities;
    } catch (e) {
        console.error('Error calculating net worth:', e);
        return 0;
    }
}

function calculateProjected(txs, type, months) {
    try {
        const now = new Date();
        return Array(months).fill(0).map((_, i) => {
            const month = new Date(now);
            month.setMonth(now.getMonth() + i + 1);
            
            return txs
                .filter(tx => (tx.transaction_type || tx.type) === type)
                .reduce((sum, tx) => {
                    const freq = tx.frequency;
                    let multiplier = 0;
                    
                    if (freq === 'monthly') multiplier = 1;
                    else if (freq === 'weekly') multiplier = 4;
                    else if (freq === 'daily') multiplier = 30;
                    else if (freq === 'yearly' && 
                            new Date(tx.date).getMonth() === month.getMonth()) multiplier = 1;
                    
                    return sum + (Math.abs(Number(tx.amount)) * multiplier);
                }, 0);
        });
    } catch (e) {
        console.error('Error calculating projected values:', e);
        return Array(months).fill(0);
    }
}

function calculateNetProjection(txs, months) {
    try {
        const income = calculateProjected(txs, 'income', months);
        const expenses = calculateProjected(txs, 'expense', months);
        let runningTotal = 0;
        
        return income.map((val, i) => {
            runningTotal += val - expenses[i];
            return runningTotal;
        });
    } catch (e) {
        console.error('Error calculating net projection:', e);
        return Array(months).fill(0);
    }
}

// Timeframe Selectors
function initTimeframeSelectors() {
    const timeframeBtns = document.querySelectorAll('.timeframe-btn');
    if (timeframeBtns.length === 0) {
        console.warn('No timeframe buttons found');
        return;
    }

    timeframeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            timeframeBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Here you would typically filter data based on timeframe
            // For now we'll just log the selection
            console.log('Timeframe selected:', this.textContent.trim());
            
            // Example of how you might implement filtering:
            // updateChartsForTimeframe(this.textContent.trim());
        });
    });
}