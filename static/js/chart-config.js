/**
 * Chart.js configuration and setup
 */

// Default colors for charts
const chartColors = {
  primary: '#2a41e8',
  secondary: '#4d84ff',
  success: '#28a745',
  warning: '#ffc107',
  danger: '#dc3545',
  info: '#17a2b8',
  light: '#f8f9fa',
  dark: '#343a40',
  gray: '#6c757d'
};

// Global Chart.js configuration
if (typeof Chart !== 'undefined') {
  Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
  Chart.defaults.font.size = 14;
  Chart.defaults.color = '#6c757d';
  Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.7)';
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 4;
  Chart.defaults.plugins.tooltip.titleFont = {
    weight: 'bold'
  };
}

// Function to create a progress chart
function createProgressChart(elementId, progress, total, color = chartColors.primary) {
  const canvas = document.getElementById(elementId);
  if (!canvas) return null;
  
  const percentage = total > 0 ? (progress / total) * 100 : 0;
  
  return new Chart(canvas, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [percentage, 100 - percentage],
        backgroundColor: [color, '#f0f0f0'],
        borderWidth: 0
      }]
    },
    options: {
      cutout: '75%',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          enabled: false
        }
      }
    }
  });
}

// Function to create a student activity chart
function createActivityChart(elementId, data) {
  const canvas = document.getElementById(elementId);
  if (!canvas) return null;
  
  return new Chart(canvas, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Activity Hours',
        data: data.values,
        borderColor: chartColors.primary,
        backgroundColor: hexToRgba(chartColors.primary, 0.1),
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

// Function to create a grades chart
function createGradesChart(elementId, data) {
  const canvas = document.getElementById(elementId);
  if (!canvas) return null;
  
  return new Chart(canvas, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Grades',
        data: data.values,
        backgroundColor: data.values.map(value => {
          if (value >= 90) return chartColors.success;
          if (value >= 70) return chartColors.primary;
          if (value >= 50) return chartColors.warning;
          return chartColors.danger;
        }),
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: 'Score'
          }
        }
      }
    }
  });
}

// Function to create a student distribution chart
function createStudentDistributionChart(elementId, data) {
  const canvas = document.getElementById(elementId);
  if (!canvas) return null;
  
  return new Chart(canvas, {
    type: 'pie',
    data: {
      labels: data.labels,
      datasets: [{
        data: data.values,
        backgroundColor: [
          chartColors.primary,
          chartColors.secondary,
          chartColors.success,
          chartColors.warning,
          chartColors.danger,
          chartColors.info
        ]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right'
        }
      }
    }
  });
}

// Utility function to convert hex color to rgba
function hexToRgba(hex, alpha = 1) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
