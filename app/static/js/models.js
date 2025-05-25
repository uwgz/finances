// static/js/transactions.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize modal functionality
    const transactionType = document.getElementById('transaction_type');
    if (transactionType) {
        transactionType.addEventListener('change', function() {
            const type = this.value;
            const categorySelect = document.getElementById('category');
            categorySelect.innerHTML = '<option value="" disabled selected>Select category</option>';
            
            const categories = {
                income: ['Salary', 'Bonus', 'Investment', 'Freelance Work', 'Rental Income', 'Dividends', 'Interest Income', 'Capital Gains', 'Pension', 'Government Benefits', 'Royalties', 'Alimony/Child Support', 'Other Income'],
                expense: ['Food', 'Transportation', 'Housing', 'Utilities', 'Entertainment', 'Healthcare', 'Insurance', 'Debt Payments', 'Education', 'Clothing', 'Travel', 'Subscriptions', 'Gifts & Donations', 'Childcare', 'Savings Contributions', 'Personal Care', 'Taxes', 'Miscellaneous'],
                assets: ['Real Estate', 'Stocks', 'Savings', 'Cash', 'Bonds', 'Mutual Funds', 'Retirement Accounts (e.g., RRSP, 401(k))', 'Precious Metals', 'Collectibles', 'Vehicles', 'Business Ownership', 'Cryptocurrency', 'Intellectual Property', 'Other Assets']

            };
            
            if (type && categories[type]) {
                categories[type].forEach(category => {
                    const option = document.createElement('option');
                    option.value = category.toLowerCase().replace(' ', '_');
                    option.textContent = category;
                    categorySelect.appendChild(option);
                });
            }
        });
    }
});

function openTransactionModal() {
    document.getElementById('transactionModal').style.display = 'block';
    document.getElementById('date').valueAsDate = new Date();
}

function closeModal() {
    document.getElementById('transactionModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('transactionModal');
    if (event.target == modal) {
        closeModal();
    }
}