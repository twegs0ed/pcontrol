// static/js/camera_widget.js
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем поддержку камеры
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.warn('Камера не поддерживается в этом браузере');
        // Показываем сообщение пользователю
        const messages = document.querySelectorAll('.camera-file-input');
        messages.forEach(input => {
            const wrapper = input.closest('.file-input-wrapper');
            const msg = document.createElement('div');
            msg.className = 'alert alert-warning mt-2';
            msg.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Камера не поддерживается. Используйте загрузку файлов.';
            wrapper.parentNode.insertBefore(msg, wrapper.nextSibling);
        });
    }
});