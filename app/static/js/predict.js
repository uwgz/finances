document.getElementById('goal-form').addEventListener('submit', function(e) {
    e.preventDefault(); // Prevent default form submission
    
    // Get form values
    const goalName = document.getElementById('goal-name').value;
    const goalAmount = parseFloat(document.getElementById('goal-amount').value);
    
    // Get transactions data from hidden input
    const transactionsData = JSON.parse(document.getElementById('transactions-data').value);
    
    // Prepare the data to send
    const requestData = {
        goal_name: goalName,
        goal_amount: goalAmount,
        transactions: transactionsData
    };
    
    // Send to backend
    fetch('/dashboard/feeds/predictor', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        // Handle success (show message, redirect, etc.)
    })
    .catch((error) => {
        console.error('Error:', error);
        // Handle error
    });
});