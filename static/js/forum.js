/**
 * Forum functionality JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle like button clicks
    document.querySelectorAll('.like-button').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const responseId = this.getAttribute('data-response-id');
            const likeCount = this.querySelector('.like-count');
            const likeIcon = this.querySelector('i');
            
            fetch(`/forum/response/${responseId}/like`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                // Update like count
                likeCount.textContent = data.count;
                
                // Update button appearance
                if (data.liked) {
                    likeIcon.classList.remove('far');
                    likeIcon.classList.add('fas');
                    this.classList.add('active');
                } else {
                    likeIcon.classList.remove('fas');
                    likeIcon.classList.add('far');
                    this.classList.remove('active');
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
    
    // Handle solution marking
    document.querySelectorAll('.mark-solution').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const responseId = this.getAttribute('data-response-id');
            const responseElement = document.querySelector(`#response-${responseId}`);
            
            fetch(`/forum/response/${responseId}/mark-solution`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.is_solution) {
                    responseElement.classList.add('solution');
                    this.innerHTML = '<i class="fas fa-check-circle me-1"></i>Marked as Solution';
                    this.classList.add('active');
                } else {
                    responseElement.classList.remove('solution');
                    this.innerHTML = '<i class="far fa-check-circle me-1"></i>Mark as Solution';
                    this.classList.remove('active');
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });

    // Rich text editor initialization for forum posts (if available)
    const textareas = document.querySelectorAll('textarea.rich-editor');
    if (textareas.length > 0 && typeof CKEDITOR !== 'undefined') {
        textareas.forEach(textarea => {
            CKEDITOR.replace(textarea.id, {
                toolbar: [
                    { name: 'basicstyles', items: ['Bold', 'Italic', 'Underline', 'Strike'] },
                    { name: 'paragraph', items: ['NumberedList', 'BulletedList', '-', 'Blockquote'] },
                    { name: 'links', items: ['Link', 'Unlink'] },
                    { name: 'insert', items: ['Table', 'HorizontalRule', 'SpecialChar'] },
                    { name: 'tools', items: ['Maximize'] },
                ]
            });
        });
    }
});
