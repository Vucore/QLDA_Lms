document.addEventListener('DOMContentLoaded', function () {
    const imageInput = document.getElementById('course_image');
    const previewContainer = document.createElement('div');
    previewContainer.className = 'mt-2 d-none';
    previewContainer.innerHTML = `
        <img id="imagePreview" src="#" alt="Preview" class="img-thumbnail" style="max-height: 200px">
        <div class="form-text">Preview</div>
    `;

    if (imageInput) {
        imageInput.parentNode.appendChild(previewContainer);

        imageInput.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (file) {
                // Validate file type
                if (!file.type.startsWith('image/')) {
                    alert('Please select an image file');
                    this.value = '';
                    return;
                }

                // Validate file size (2MB)
                if (file.size > 2 * 1024 * 1024) {
                    alert('File size must be less than 2MB');
                    this.value = '';
                    return;
                }

                const reader = new FileReader();
                reader.onload = function (e) {
                    const preview = document.getElementById('imagePreview');
                    preview.src = e.target.result;
                    previewContainer.classList.remove('d-none');
                }
                reader.readAsDataURL(file);
            } else {
                previewContainer.classList.add('d-none');
            }
        });
    }
});
