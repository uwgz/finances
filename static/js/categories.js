function updateCategories() {
    const type = document.getElementById('type').value;
    const categorySelect = document.getElementById('category');
    
    // Clear existing options while preserving the placeholder
    categorySelect.innerHTML = '<option value="" disabled selected>Select a category</option>';
    
    // Organized category data structure
    const categories = {
        income: {
            'Primary Income': ["Salary", "Bonus", "Commission", "Freelance"],
            'Investment Income': ["Dividends", "Interest", "Capital Gains", "Rental Income"],
            'Other Income': ["Gifts", "Tax Refund", "Reimbursement", "Side Hustle"]
        },
        expense: {
            'Essentials': ["Rent/Mortgage", "Utilities", "Groceries", "Transportation"],
            'Healthcare': ["Health Insurance", "Doctor Visits", "Medications"],
            'Lifestyle': ["Dining Out", "Entertainment", "Hobbies", "Vacation"]
        }
    };

    // Add categorized options if type is selected
    if (type && categories[type]) {
        for (const [groupName, groupCategories] of Object.entries(categories[type])) {
            const group = document.createElement('optgroup');
            group.label = groupName;
            
            groupCategories.forEach(cat => {
                const option = new Option(cat, cat);
                // Add data-type for validation if needed
                option.dataset.type = type; 
                group.appendChild(option);
            });
            
            categorySelect.appendChild(group);
        }
    }

    // Enable the select if type is chosen
    categorySelect.disabled = !type;
}

// Initialize on page load and type change
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('type').addEventListener('change', updateCategories);
    updateCategories(); // Initialize in case type is pre-selected
});