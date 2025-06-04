/**
 * Course form handling for EduLearn LMS
 * Manages dynamic schedule creation and form validation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle adding new schedule items
    const addScheduleBtn = document.getElementById('add-schedule');
    const scheduleItemsContainer = document.getElementById('schedule-items');
    
    if (addScheduleBtn && scheduleItemsContainer) {
        addScheduleBtn.addEventListener('click', function() {
            const scheduleTemplate = `
                <div class="schedule-item mb-3 p-3 border rounded">
                    <div class="row g-2">
                        <div class="col-md-3">
                            <label class="form-label">Day</label>
                            <select class="form-select" name="schedule_day[]">
                                <option value="Monday">Monday</option>
                                <option value="Tuesday">Tuesday</option>
                                <option value="Wednesday">Wednesday</option>
                                <option value="Thursday">Thursday</option>
                                <option value="Friday">Friday</option>
                                <option value="Saturday">Saturday</option>
                                <option value="Sunday">Sunday</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Start Time</label>
                            <input type="time" class="form-control" name="schedule_start_time[]">
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">End Time</label>
                            <input type="time" class="form-control" name="schedule_end_time[]">
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Location</label>
                            <input type="text" class="form-control" name="schedule_location[]" placeholder="Optional">
                        </div>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-danger mt-2 remove-schedule">
                        <i class="fas fa-times me-1"></i>Remove
                    </button>
                </div>
            `;
            
            // Insert the new schedule item
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = scheduleTemplate.trim();
            const newItem = tempDiv.firstElementChild;
            scheduleItemsContainer.appendChild(newItem);
            
            // Add event listener to the remove button
            newItem.querySelector('.remove-schedule').addEventListener('click', function() {
                newItem.remove();
            });
        });
        
        // Add event listeners to any initial remove buttons
        document.querySelectorAll('.remove-schedule').forEach(button => {
            button.addEventListener('click', function() {
                this.closest('.schedule-item').remove();
            });
        });
    }
    
    // Form validation
    const form = document.querySelector('form.needs-validation');
    if (form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    }
});