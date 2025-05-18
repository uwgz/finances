// DOM ready event
document.addEventListener('DOMContentLoaded', function() {
    // Close alert messages
    const closeButtons = document.querySelectorAll('.close-btn');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const alert = this.parentElement;
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 300);
        });
    });

    // Toggle dropdown menus
    const userProfile = document.querySelector('.user-profile');
    if (userProfile) {
        userProfile.addEventListener('click', function(e) {
            e.stopPropagation();
            const dropdown = this.querySelector('.dropdown-menu');
            dropdown.classList.toggle('active');
        });
    }

    // Close dropdowns when clicking outside
    document.addEventListener('click', function() {
        const dropdowns = document.querySelectorAll('.dropdown-menu');
        dropdowns.forEach(dropdown => {
            dropdown.classList.remove('active');
        });
    });

    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.toggle('active');
        });
    }
});