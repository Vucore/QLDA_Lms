/**
 * Sửa lỗi modal-fade bị nhảy khi di chuột 
 */
document.addEventListener('DOMContentLoaded', function() {
    // Tìm tất cả các modal trong trang
    var modals = document.querySelectorAll('.modal');
    
    // Khởi tạo các modal với tùy chọn tối ưu
    modals.forEach(function(modal) {
        // Ngăn modal đóng khi click bên ngoài
        var modalInstance = new bootstrap.Modal(modal, {
            backdrop: 'static',  // Không đóng khi click bên ngoài
            keyboard: false      // Không đóng khi nhấn Esc
        });
        
        // Tìm nút đóng modal
        var closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"]');
        closeButtons.forEach(function(button) {
            button.addEventListener('click', function() {
                modalInstance.hide();
            });
        });
    });
    
    // Xử lý các nút mở modal
    var modalTriggers = document.querySelectorAll('[data-bs-toggle="modal"]');
    modalTriggers.forEach(function(trigger) {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            var targetSelector = trigger.getAttribute('data-bs-target');
            var target = document.querySelector(targetSelector);
            if (target) {
                var modalInstance = bootstrap.Modal.getInstance(target) || new bootstrap.Modal(target, {
                    backdrop: 'static',
                    keyboard: false
                });
                modalInstance.show();
            }
        });
    });
    
    // Ngăn chặn sự kiện bubbling cho các nút trong modal
    var modalButtons = document.querySelectorAll('.modal .btn');
    modalButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
});