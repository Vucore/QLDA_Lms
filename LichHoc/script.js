document.addEventListener('DOMContentLoaded', function() {
    // Initialize current month and year
    const currentDate = new Date();
    let currentMonth = currentDate.getMonth();
    let currentYear = currentDate.getFullYear();
    
    // Navigation functionality
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all items
            navItems.forEach(nav => nav.classList.remove('active'));
            // Add active class to clicked item
            this.classList.add('active');
            
            // In a real app, we would navigate to the corresponding page
            const pageName = this.querySelector('span').textContent;
            console.log(`Navigating to ${pageName} page...`);
        });
    });
    
    // Calendar navigation
    const prevBtn = document.querySelector('.prev-btn');
    const nextBtn = document.querySelector('.next-btn');
    const calendarTitle = document.querySelector('.calendar-section .section-title');
    
    if (prevBtn && nextBtn && calendarTitle) {
        prevBtn.addEventListener('click', function() {
            currentMonth--;
            if (currentMonth < 0) {
                currentMonth = 11;
                currentYear--;
            }
            updateCalendarTitle(currentMonth, currentYear);
            console.log(`Showing calendar for ${getMonthName(currentMonth)}, ${currentYear}`);
            // In a real app, we would update the calendar grid
        });
        
        nextBtn.addEventListener('click', function() {
            currentMonth++;
            if (currentMonth > 11) {
                currentMonth = 0;
                currentYear++;
            }
            updateCalendarTitle(currentMonth, currentYear);
            console.log(`Showing calendar for ${getMonthName(currentMonth)}, ${currentYear}`);
            // In a real app, we would update the calendar grid
        });
    }
    
    // Calendar day events
    const daysWithEvents = document.querySelectorAll('.day.has-event');
    
    daysWithEvents.forEach(day => {
        day.addEventListener('click', function() {
            const dayNumber = this.querySelector('.day-number').textContent;
            const eventName = this.querySelector('.event-name').textContent.replace(/\s+/g, ' ').trim();
            const eventTime = this.querySelector('.event-time').textContent.replace(/\s+/g, ' ').trim();
            
            console.log(`Clicked on day ${dayNumber} with event: ${eventName} at ${eventTime}`);
            
            // In a real app, we might show a modal with event details
            alert(`Chi tiết sự kiện:\n${eventName}\nNgày: ${dayNumber}/${currentMonth + 1}/${currentYear}\nThời gian: ${eventTime}`);
        });
    });
    
    // Enter class buttons
    const enterClassBtns = document.querySelectorAll('.enter-class-btn');
    
    enterClassBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const classCard = this.closest('.class-card');
            const className = classCard.querySelector('.class-title').textContent;
            const classSchedule = classCard.querySelector('.class-schedule').textContent;
            const classLocation = classCard.querySelector('.class-location').textContent;
            
            console.log(`Entering class: ${className}`);
            console.log(`Schedule: ${classSchedule}`);
            console.log(`Location: ${classLocation}`);
            
            // In a real app, we would redirect to a virtual classroom
            alert(`Đang vào lớp học: ${className}\n${classSchedule}\n${classLocation}`);
            
            // Simulate loading
            this.innerHTML = '<span>Đang tải...</span>';
            this.disabled = true;
            
            // Reset after 2 seconds
            setTimeout(() => {
                this.innerHTML = '<span>Vào lớp</span><img src="assets/enter-class.svg" alt="Vào lớp">';
                this.disabled = false;
            }, 2000);
        });
    });
    
    // Helper functions
    function updateCalendarTitle(month, year) {
        const monthName = getMonthName(month);
        if (calendarTitle) {
            calendarTitle.textContent = `Lịch học tháng ${month + 1}, ${year}`;
        }
    }
    
    function getMonthName(monthIndex) {
        const months = [
            'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
            'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
        ];
        return months[monthIndex];
    }
    
    // User profile interaction
    const userProfile = document.querySelector('.user-profile');
    
    if (userProfile) {
        userProfile.addEventListener('click', function() {
            // In a real app, we would show a dropdown menu
            console.log('User profile clicked');
            alert('Tùy chọn người dùng hiện lên ở đây');
        });
    }
    
    // Notification button interaction
    const notificationBtn = document.querySelector('.notification-btn');
    
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function() {
            // In a real app, we would show notifications
            console.log('Notification button clicked');
            alert('Thông báo hiện lên ở đây');
        });
    }
}); 