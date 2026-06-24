// static/js/ajax_form.js
class AjaxFormHandler {
    constructor(options = {}) {
        this.objectId = options.objectId || null;
        this.namespace = options.namespace || 'gs14';
        this.csrfToken = options.csrfToken || document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        
        this.initImageUploads();
        this.initTitleAutoSave();
        this.initStatusCheck();
    }
    
    // Инициализация загрузки изображений
    initImageUploads() {
        const imageInputs = document.querySelectorAll('input[type="file"][id^="id_image"], input[type="file"][id="id_serial_photo"]');
        
        imageInputs.forEach(input => {
            // Убираем старые обработчики
            const newInput = input.cloneNode(true);
            input.parentNode.replaceChild(newInput, input);
            
            newInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (!file) return;
                
                // Определяем поле
                const fieldName = newInput.id.replace('id_', '');
                
                // Создаем превью
                const previewId = `preview_${fieldName}`;
                const previewContainer = document.getElementById(previewId);
                if (previewContainer) {
                    const reader = new FileReader();
                    reader.onload = function(ev) {
                        const img = previewContainer.querySelector('img');
                        if (img) {
                            img.src = ev.target.result;
                        }
                        previewContainer.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                }
                
                // Отправляем на сервер
                this.uploadImage(fieldName, file);
            });
        });
    }
    
    // Загрузка изображения через AJAX
    uploadImage(fieldName, file) {
        const formData = new FormData();
        formData.append(fieldName, file);
        formData.append('csrfmiddlewaretoken', this.csrfToken);
        
        // Показываем индикатор загрузки
        this.showFieldLoading(fieldName, true);
        
        const url = `/${this.namespace}/ajax-save-image/${this.objectId}/${fieldName}/`;
        
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            this.showFieldLoading(fieldName, false);
            
            if (data.success) {
                this.showNotification('success', data.message);
                
                // Обновляем изображение
                if (data.image_url) {
                    const currentImg = document.getElementById(`current_${fieldName}`);
                    if (currentImg) {
                        currentImg.src = data.image_url;
                        currentImg.style.display = 'block';
                    }
                    const noImg = document.getElementById(`no_${fieldName}`);
                    if (noImg) noImg.style.display = 'none';
                }
                
                // Проверяем статус
                if (data.is_completed) {
                    this.showNotification('success', '✅ Все фото загружены! Объект завершен.');
                    this.updateStatus(data.status, data.status_display);
                }
            } else {
                this.showNotification('danger', data.error || 'Ошибка загрузки изображения');
            }
        })
        .catch(error => {
            this.showFieldLoading(fieldName, false);
            this.showNotification('danger', 'Ошибка сети: ' + error.message);
        });
    }
    
    // Инициализация автосохранения заголовков
    initTitleAutoSave() {
        const titleInputs = document.querySelectorAll('input[id^="id_title"], textarea[id="id_description"]');
        
        let saveTimeout = null;
        
        titleInputs.forEach(input => {
            input.addEventListener('input', () => {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(() => {
                    const fieldName = input.id.replace('id_', '');
                    this.saveTitle(fieldName, input.value);
                }, 500);
            });
            
            // Сохраняем при потере фокуса
            input.addEventListener('blur', () => {
                clearTimeout(saveTimeout);
                const fieldName = input.id.replace('id_', '');
                this.saveTitle(fieldName, input.value);
            });
        });
    }
    
    // Сохранение заголовка через AJAX
    saveTitle(fieldName, value) {
        const url = `/${this.namespace}/ajax-save-title/${this.objectId}/${fieldName}/`;
        
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify({ value: value })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('Ошибка сохранения заголовка:', data.error);
            }
        })
        .catch(error => {
            console.error('Ошибка сети:', error);
        });
    }
    
    // Проверка статуса объекта
    initStatusCheck() {
        // Проверяем статус каждые 5 секунд
        setInterval(() => {
            this.checkStatus();
        }, 5000);
    }
    
    checkStatus() {
        if (!this.objectId) return;
        
        const url = `/${this.namespace}/ajax-check-completed/${this.objectId}/`;
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': this.csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.is_completed) {
                this.updateStatus(data.status, data.status_display);
            }
        })
        .catch(error => {
            console.error('Ошибка проверки статуса:', error);
        });
    }
    
    // Вспомогательные методы
    showFieldLoading(fieldName, isLoading) {
        const input = document.getElementById(`id_${fieldName}`);
        if (input) {
            if (isLoading) {
                input.disabled = true;
                input.style.opacity = '0.5';
            } else {
                input.disabled = false;
                input.style.opacity = '1';
            }
        }
    }
    
    showNotification(type, message) {
        const container = document.getElementById('form-messages');
        if (!container) return;
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        container.appendChild(alert);
        
        // Автоматическое скрытие через 5 секунд
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
    
    updateStatus(status, statusDisplay) {
        // Обновляем статус в UI
        const statusBadge = document.querySelector('.badge-status');
        if (statusBadge) {
            statusBadge.className = `badge-status ${status}`;
            statusBadge.textContent = statusDisplay;
        }
        
        // Обновляем блок статуса
        const statusBlock = document.querySelector('.card.mb-3 .d-flex.justify-content-between');
        if (statusBlock) {
            // Можно обновить содержимое блока статуса
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    const objectId = document.querySelector('[data-object-id]')?.dataset?.objectId || null;
    const namespace = document.querySelector('[data-namespace]')?.dataset?.namespace || 'gs14';
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    
    // Инициализируем AJAX обработчик только если есть objectId (редактирование)
    if (objectId) {
        window.ajaxHandler = new AjaxFormHandler({
            objectId: objectId,
            namespace: namespace,
            csrfToken: csrfToken
        });
    }
});