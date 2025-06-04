/**
 * Course detail page specific JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
  // Đã loại bỏ code xử lý accordion vì đã chuyển sang dùng trang chi tiết bài giảng
  
  // Course tabs
  const courseTabs = document.querySelectorAll('.course-tab');
  const courseTabContents = document.querySelectorAll('.course-tab-content');
  
  if (courseTabs.length > 0) {
    courseTabs.forEach(tab => {
      tab.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Remove active class from all tabs
        courseTabs.forEach(t => {
          t.classList.remove('active');
        });
        
        // Hide all tab contents
        courseTabContents.forEach(content => {
          content.classList.remove('active');
        });
        
        // Add active class to clicked tab
        this.classList.add('active');
        
        // Show corresponding tab content
        const contentId = this.getAttribute('data-tab');
        const content = document.getElementById(contentId);
        if (content) {
          content.classList.add('active');
        }
      });
    });
    
    // Activate first tab by default
    courseTabs[0]?.click();
  }
  
  // Video player functionality
  const videoPlayers = document.querySelectorAll('.course-video');
  
  videoPlayers.forEach(player => {
    const playButton = player.querySelector('.play-button');
    const videoContainer = player.querySelector('.video-container');
    
    if (playButton && videoContainer) {
      playButton.addEventListener('click', function() {
        // Replace image with actual video embed (in a real app)
        const videoId = player.getAttribute('data-video-id');
        const videoUrl = player.getAttribute('data-video-url');
        
        if (videoUrl) {
          // This is a simplified example; in a real app, you would embed the actual video player
          videoContainer.innerHTML = `
            <div class="ratio ratio-16x9">
              <iframe 
                src="${videoUrl}" 
                title="Course video" 
                allowfullscreen
              ></iframe>
            </div>
          `;
        }
      });
    }
  });
  
  // Course enrollment button
  const enrollButton = document.getElementById('enroll-button');
  
  if (enrollButton) {
    enrollButton.addEventListener('click', function() {
      const courseId = this.getAttribute('data-course-id');
      const enrollmentForm = document.getElementById('enrollment-form');
      
      if (enrollmentForm) {
        enrollmentForm.submit();
      }
    });
  }
  
  // Rating functionality
  const ratingStars = document.querySelectorAll('.rating-star');
  const ratingInput = document.getElementById('rating-input');
  
  if (ratingStars.length > 0 && ratingInput) {
    ratingStars.forEach(star => {
      star.addEventListener('click', function() {
        const value = this.getAttribute('data-value');
        ratingInput.value = value;
        
        // Update UI
        ratingStars.forEach(s => {
          const starValue = s.getAttribute('data-value');
          if (starValue <= value) {
            s.classList.remove('far');
            s.classList.add('fas');
          } else {
            s.classList.remove('fas');
            s.classList.add('far');
          }
        });
      });
      
      // Hover effects
      star.addEventListener('mouseenter', function() {
        const value = this.getAttribute('data-value');
        
        ratingStars.forEach(s => {
          const starValue = s.getAttribute('data-value');
          if (starValue <= value) {
            s.classList.add('hover');
          }
        });
      });
      
      star.addEventListener('mouseleave', function() {
        ratingStars.forEach(s => {
          s.classList.remove('hover');
        });
      });
    });
  }
  
  // Lesson completion tracking
  const lessonItems = document.querySelectorAll('.lesson-item');
  
  lessonItems.forEach(item => {
    const checkbox = item.querySelector('.lesson-complete-checkbox');
    
    if (checkbox) {
      checkbox.addEventListener('change', function() {
        const lessonId = this.getAttribute('data-lesson-id');
        const isChecked = this.checked;
        
        // In a real app, make an AJAX request to update completion status
        console.log(`Lesson ${lessonId} marked as ${isChecked ? 'complete' : 'incomplete'}`);
        
        // Update UI
        if (isChecked) {
          item.classList.add('completed');
        } else {
          item.classList.remove('completed');
        }
      });
    }
  });
});
