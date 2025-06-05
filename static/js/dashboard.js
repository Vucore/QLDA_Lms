/**
 * Dashboard specific JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
  
  // Initialize progress charts if they exist
  const progressCharts = document.querySelectorAll('.progress-chart');
  
  if (progressCharts.length > 0) {
    progressCharts.forEach(chartCanvas => {
      const courseId = chartCanvas.getAttribute('data-course-id');
      const completedLessons = parseInt(chartCanvas.getAttribute('data-completed'), 10);
      const totalLessons = parseInt(chartCanvas.getAttribute('data-total'), 10);
      
      new Chart(chartCanvas, {
        type: 'doughnut',
        data: {
          labels: ['Completed', 'Remaining'],
          datasets: [{
            data: [completedLessons, totalLessons - completedLessons],
            backgroundColor: ['#2a41e8', '#e9ecef'],
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '75%',
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const value = context.raw;
                  const percentage = Math.round((value / totalLessons) * 100);
                  return `${value} lessons (${percentage}%)`;
                }
              }
            }
          }
        }
      });
      
      // Add center text
      const centerText = document.getElementById(`progress-text-${courseId}`);
      if (centerText) {
        const percentage = Math.round((completedLessons / totalLessons) * 100);
        centerText.textContent = `${percentage}%`;
      }
    });
  }
  
  // Learning goals progress bars
  const goalProgressBars = document.querySelectorAll('.goal-progress');
  
  goalProgressBars.forEach(progressBar => {
    const progress = parseInt(progressBar.getAttribute('data-progress'), 10);
    progressBar.style.width = `${progress}%`;
    
    if (progress < 30) {
      progressBar.classList.add('bg-danger');
    } else if (progress < 70) {
      progressBar.classList.add('bg-warning');
    } else {
      progressBar.classList.add('bg-success');
    }
  });
  
  // Calendar view functionality
  const calendarDays = document.querySelectorAll('.calendar-day');
  const calendarEvents = document.querySelectorAll('.calendar-event');
  
  if (calendarDays.length > 0) {
    calendarDays.forEach(day => {
      day.addEventListener('click', function() {
        const date = this.getAttribute('data-date');
        
        // Hide all events
        calendarEvents.forEach(event => {
          event.style.display = 'none';
        });
        
        // Show events for selected date
        const eventsForDay = document.querySelectorAll(`.calendar-event[data-date="${date}"]`);
        eventsForDay.forEach(event => {
          event.style.display = 'block';
        });
        
        // Highlight selected day
        calendarDays.forEach(d => {
          d.classList.remove('selected');
        });
        this.classList.add('selected');
      });
    });
    
    // Select current day by default
    const today = new Date().toISOString().split('T')[0];
    const currentDay = document.querySelector(`.calendar-day[data-date="${today}"]`);
    
    if (currentDay) {
      currentDay.click();
    } else {
      // If current day not found, click the first day
      calendarDays[0]?.click();
    }
  }
  
  // Toggle course content sections
  const contentToggles = document.querySelectorAll('.content-toggle');
  
  contentToggles.forEach(toggle => {
    toggle.addEventListener('click', function() {
      const contentId = this.getAttribute('data-target');
      const content = document.getElementById(contentId);
      
      if (content) {
        content.classList.toggle('show');
        
        // Toggle icon
        const icon = this.querySelector('i');
        if (icon) {
          icon.classList.toggle('fa-chevron-down');
          icon.classList.toggle('fa-chevron-up');
        }
      }
    });
  });
  
  // Mark lesson as completed
  const lessonCompletionButtons = document.querySelectorAll('.mark-complete');
  
  lessonCompletionButtons.forEach(button => {
    button.addEventListener('click', function() {
      const lessonId = this.getAttribute('data-lesson-id');
      const isCompleted = this.classList.contains('completed');
      
      // Toggle button state
      this.classList.toggle('completed');
      this.textContent = isCompleted ? 'Mark as Complete' : 'Completed';
      
      // In a real application, send an AJAX request to update lesson completion status
      // This is a placeholder for demonstration
      console.log(`Lesson ${lessonId} marked as ${isCompleted ? 'incomplete' : 'complete'}`);
    });
  });
  
  // Handler for assignment submission form
  const submissionForm = document.getElementById('submission-form');
  
  if (submissionForm) {
    submissionForm.addEventListener('submit', function(e) {
      const fileInput = this.querySelector('input[type="file"]');
      const contentInput = this.querySelector('textarea');
      
      if (!fileInput.files.length && !contentInput.value.trim()) {
        e.preventDefault();
        alert('Please upload a file or enter submission content');
      }
    });
  }
  
  // Initialize activity chart for student dashboard
  const activityChartCanvas = document.getElementById('activity-chart');
  
  if (activityChartCanvas) {
    const ctx = activityChartCanvas.getContext('2d');
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
        datasets: [{
          label: 'Hours Spent',
          data: [5, 8, 6, 9, 12, 7],
          borderColor: '#2a41e8',
          backgroundColor: 'rgba(42, 65, 232, 0.1)',
          tension: 0.3,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Hours'
            }
          }
        },
        plugins: {
          legend: {
            display: false
          }
        }
      }
    });
  }
  
  // Add event listener for "Schedule" navigation item
  const scheduleNavItem = document.getElementById('schedule-nav-item');
  if (scheduleNavItem) {
    scheduleNavItem.addEventListener('click', function() {
      const scheduleUrl = scheduleNavItem.getAttribute('href');
      if (scheduleUrl) {
        window.location.href = scheduleUrl;
      }
    });
  }
});
