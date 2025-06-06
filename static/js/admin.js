/**
 * Admin specific JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all modals
    var modals = document.querySelectorAll('.modal');
    modals.forEach(function(modal) {
        new bootstrap.Modal(modal);
    });

    // Initialize dropdowns
    var dropdowns = document.querySelectorAll('.dropdown-toggle');
    dropdowns.forEach(function(dropdown) {
        new bootstrap.Dropdown(dropdown);
    });

    // Filter courses by instructor
    const instructorFilter = document.querySelector('.form-select');
    if (instructorFilter) {
        instructorFilter.addEventListener('change', function() {
            const selectedInstructorId = this.value;
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                if (selectedInstructorId === 'all') {
                    row.style.display = '';
                } else {
                    const instructorCell = row.querySelector('td:nth-child(2)');
                    const instructorId = instructorCell.getAttribute('data-instructor-id');
                    
                    if (instructorId === selectedInstructorId) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                }
            });
        });
    }

    // Search functionality
    const searchInput = document.querySelector('input[placeholder="Search courses..."]');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const courseName = row.querySelector('td:first-child').textContent.toLowerCase();
                if (courseName.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Search courses by name
    const searchInputByName = document.querySelector('.form-control');
    if (searchInputByName) {
        searchInputByName.addEventListener('input', function() {
            const searchQuery = this.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const courseNameCell = row.querySelector('td:nth-child(1)');
                const courseName = courseNameCell.textContent.toLowerCase();

                if (courseName.includes(searchQuery)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
});
