/**
 * Main JavaScript file for the EduLearn application
 */

// Wait for the document to be fully loaded
document.addEventListener('DOMContentLoaded', function () {

  // Add smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      // Skip if href is just "#"
      if (href === '#') return;

      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        window.scroll({
          top: target.offsetTop - 70,
          behavior: 'smooth'
        });
      }
    });
  });

  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Initialize popovers
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });

  // Auto-hide flash messages after 5 seconds
  // Alert behavior is now handled in alert.js

  // Toggle search form on small screens
  const searchToggle = document.getElementById('search-toggle');
  const searchForm = document.getElementById('search-form');

  if (searchToggle && searchForm) {
    searchToggle.addEventListener('click', function (e) {
      e.preventDefault();
      searchForm.classList.toggle('d-none');
    });
  }

  // Course filter functionality
  const courseFilter = document.getElementById('course-filter');
  const courseCards = document.querySelectorAll('.course-card');

  if (courseFilter && courseCards.length > 0) {
    courseFilter.addEventListener('change', function () {
      const category = this.value;

      courseCards.forEach(card => {
        const cardCategory = card.getAttribute('data-category');

        if (category === 'all' || cardCategory === category) {
          card.closest('.course-card-wrapper').style.display = 'block';
        } else {
          card.closest('.course-card-wrapper').style.display = 'none';
        }
      });
    });
  }

  // Course search functionality
  const courseSearch = document.getElementById('course-search');

  if (courseSearch && courseCards.length > 0) {
    courseSearch.addEventListener('input', function () {
      const searchTerm = this.value.toLowerCase().trim();

      courseCards.forEach(card => {
        const cardTitle = card.querySelector('.card-title').textContent.toLowerCase();
        const cardInstructor = card.querySelector('.course-instructor').textContent.toLowerCase();
        const cardDescription = card.querySelector('.card-text').textContent.toLowerCase();

        if (
          cardTitle.includes(searchTerm) ||
          cardInstructor.includes(searchTerm) ||
          cardDescription.includes(searchTerm)
        ) {
          card.closest('.course-card-wrapper').style.display = 'block';
        } else {
          card.closest('.course-card-wrapper').style.display = 'none';
        }
      });
    });
  }

  // Password visibility toggle
  const passwordToggles = document.querySelectorAll('.password-toggle');

  passwordToggles.forEach(toggle => {
    toggle.addEventListener('click', function () {
      const input = this.previousElementSibling;
      const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
      input.setAttribute('type', type);

      // Toggle icon
      this.innerHTML = type === 'password'
        ? '<i class="fa fa-eye"></i>'
        : '<i class="fa fa-eye-slash"></i>';
    });
  });

  // Form validation styles
  const forms = document.querySelectorAll('.needs-validation');

  forms.forEach(form => {
    form.addEventListener('submit', function (event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }

      form.classList.add('was-validated');
    }, false);
  });

  // Countdown for assignment deadlines
  const deadlineCounters = document.querySelectorAll('.deadline-countdown');

  deadlineCounters.forEach(counter => {
    const deadline = new Date(counter.getAttribute('data-deadline')).getTime();

    // Update the countdown every second
    const countdownInterval = setInterval(function () {
      const now = new Date().getTime();
      const distance = deadline - now;

      // Time calculations
      const days = Math.floor(distance / (1000 * 60 * 60 * 24));
      const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((distance % (1000 * 60)) / 1000);

      // Display the result
      if (distance > 0) {
        counter.innerHTML = `${days}d ${hours}h ${minutes}m ${seconds}s`;
      } else {
        clearInterval(countdownInterval);
        counter.innerHTML = 'Deadline passed';
        counter.classList.add('text-danger');
      }
    }, 1000);
  });
});
