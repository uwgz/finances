document.addEventListener('DOMContentLoaded', function() {
        // Toggle between showing 3 items and all items
        const toggleButton = document.getElementById('toggleRecurring');
        let showingAll = false;
        
        toggleButton.addEventListener('click', function() {
            const allItems = document.querySelectorAll('.recurring-item');
            
            if (showingAll) {
                // Show only first 3 items
                allItems.forEach((item, index) => {
                    if (index < 3) {
                        item.classList.remove('hidden');
                    } else {
                        item.classList.add('hidden');
                    }
                });
                toggleButton.textContent = 'View All';
            } else {
                // Show all items
                allItems.forEach(item => {
                    item.classList.remove('hidden');
                });
                toggleButton.textContent = 'Show Less';
            }
            
            showingAll = !showingAll;
        });

        // Edit button functionality
        document.querySelectorAll('.edit-btn').forEach(editBtn => {
            editBtn.addEventListener('click', function() {
                const actionButtons = this.nextElementSibling;
                this.style.display = 'none';
                actionButtons.style.display = 'block';
            });
        });

        // Cancel button functionality
        document.querySelectorAll('.cancel-btn').forEach(cancelBtn => {
            cancelBtn.addEventListener('click', function() {
                const actionButtons = this.parentElement;
                const editBtn = actionButtons.previousElementSibling;
                actionButtons.style.display = 'none';
                editBtn.style.display = 'inline-block';
            });
        });

        // Delete button functionality
        document.querySelectorAll('.delete-btn').forEach(deleteBtn => {
            deleteBtn.addEventListener('click', function() {
                const row = this.closest('tr');
                if (confirm('Are you sure you want to delete this transaction?')) {
                    // You'll need to implement AJAX call to delete from server
                    fetch('/delete-transaction', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            transaction_id: row.dataset.id
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            row.remove();
                        }
                    });
                }
            });
        });
    });