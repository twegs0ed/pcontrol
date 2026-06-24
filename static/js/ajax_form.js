class AjaxFormHandler {
    constructor(options = {}) {
        this.objectId = options.objectId || null;
        this.namespace = options.namespace || 'kt08_9a';
        this.csrfToken = options.csrfToken || document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        this.isRedirecting = false; // Флаг для предотвращения множественных редиректов
        
        this.initImageUploads();
        this.initImageDeletion();
        this.initTitleAutoSave();
        this.initStatusCheck();
        this.initScanFunctionality();
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
                this.showPreview(fieldName, file);
                
                // Отправляем на сервер
                this.uploadImage(fieldName, file);
            });
        });
    }
    
    // Показать превью изображения
    showPreview(fieldName, file) {
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
        
        // Скрываем "Нет изображения"
        const noImg = document.getElementById(`no_${fieldName}`);
        if (noImg) noImg.style.display = 'none';
        
        // Скрываем текущее изображение
        const currentImg = document.getElementById(`current_${fieldName}`);
        if (currentImg) currentImg.style.display = 'none';
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
                
                // Проверяем, завершен ли объект
                if (data.is_completed && data.redirect_url) {
                    // Показываем сообщение о завершении
                    this.showNotification('success', data.redirect_message || '✅ Все фото загружены! Объект завершен.');
                    
                    // Обновляем статус
                    this.updateStatus(data.status, data.status_display);
                    
                    // Делаем редирект через 2 секунды
                    if (!this.isRedirecting) {
                        this.isRedirecting = true;
                        setTimeout(() => {
                            window.location.href = data.redirect_url;
                        }, 2000);
                    }
                } else if (data.is_completed) {
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
    
    // Инициализация удаления изображений
    initImageDeletion() {
        const deleteCheckboxes = document.querySelectorAll('input[type="checkbox"][id^="delete_image"], input[type="checkbox"][id="delete_serial_photo"]');
        
        deleteCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    const fieldName = e.target.id.replace('delete_', '');
                    if (confirm(`Удалить изображение для поля ${fieldName}?`)) {
                        this.deleteImage(fieldName);
                    } else {
                        e.target.checked = false;
                    }
                }
            });
        });
    }
    
    // Удаление изображения через AJAX
    deleteImage(fieldName) {
        const url = `/${this.namespace}/ajax-delete-image/${this.objectId}/${fieldName}/`;
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': this.csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification('success', data.message);
                
                // Скрываем изображение
                const currentImg = document.getElementById(`current_${fieldName}`);
                if (currentImg) currentImg.style.display = 'none';
                
                const noImg = document.getElementById(`no_${fieldName}`);
                if (noImg) noImg.style.display = 'block';
                
                // Убираем галочку
                const checkbox = document.getElementById(`delete_${fieldName}`);
                if (checkbox) checkbox.checked = false;
                
                // Очищаем input
                const input = document.getElementById(`id_${fieldName}`);
                if (input) input.value = '';
            } else {
                this.showNotification('danger', data.error || 'Ошибка удаления изображения');
            }
        })
        .catch(error => {
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
        if (!this.objectId || this.isRedirecting) return;
        
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
            if (data.success && data.is_completed && data.redirect_url) {
                // Обновляем статус
                this.updateStatus(data.status, data.status_display);
                
                // Делаем редирект
                if (!this.isRedirecting) {
                    this.isRedirecting = true;
                    this.showNotification('success', '✅ Все фото загружены! Объект завершен. Перенаправление...');
                    setTimeout(() => {
                        window.location.href = data.redirect_url;
                    }, 2000);
                }
            }
        })
        .catch(error => {
            console.error('Ошибка проверки статуса:', error);
        });
    }
    
    // Инициализация функционала сканирования
    initScanFunctionality() {
        const scanBtn = document.getElementById('scanSendBtn');
        const scanInput = document.getElementById('scanFileInput');
        const scanStatus = document.getElementById('scanStatus');
        
        if (!scanBtn || !scanInput) return;
        
        const scanSend = () => {
            const file = scanInput.files[0];
            if (!file) {
                scanStatus.style.display = 'block';
                scanStatus.innerHTML = '<div class="alert alert-warning">Сначала выберите изображение</div>';
                return;
            }
            
            const formData = new FormData();
            formData.append('scan_image', file);
            formData.append('csrfmiddlewaretoken', this.csrfToken);
            
            const serialInput = document.querySelector('#id_serial_number');
            if (serialInput && serialInput.value) {
                formData.append('serial_number', serialInput.value);
            }
            
            scanStatus.style.display = 'block';
            scanStatus.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin"></i> Загрузка и распознавание...</div>';
            
            const scanUrl = `/${this.namespace}/scan-serial/`;
            
            fetch(scanUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.serial_number) {
                        serialInput.value = data.serial_number;
                        serialInput.style.borderColor = '#28a745';
                        serialInput.style.backgroundColor = '#f0fff0';
                    }
                    
                    let html = '<div class="alert alert-success">' + (data.message || 'Найден: <strong>' + data.serial_number + '</strong>') + '</div>';
                    if (data.photo_saved) {
                        html += '<div class="alert alert-info mt-2">📸 Фото сохранено в объекте</div>';
                    }
                    scanStatus.innerHTML = html;
                    
                    if (data.serial_number) {
                        const serialPhotoInput = document.getElementById('id_serial_photo');
                        if (serialPhotoInput) {
                            serialPhotoInput.value = '';
                        }
                    }
                } else {
                    let html = '<div class="alert alert-warning">' + (data.error || 'Не удалось найти серийный номер') + '</div>';
                    if (data.photo_saved) {
                        html += '<div class="alert alert-success mt-2">📸 Фото сохранено в объекте</div>';
                    }
                    if (data.temp_object) {
                        html += '<div class="alert alert-info mt-2">Создан временный объект. Отредактируйте серийный номер.</div>';
                    }
                    scanStatus.innerHTML = html;
                }
            })
            .catch(error => {
                console.error('Ошибка сканирования:', error);
                scanStatus.innerHTML = '<div class="alert alert-danger">Ошибка: ' + error.message + '</div>';
            });
        };
        
        scanBtn.onclick = scanSend;
        
        scanInput.onchange = function() {
            if (this.files[0]) {
                this.style.borderColor = '#17a2b8';
                this.style.backgroundColor = '#f0f8ff';
                setTimeout(scanSend, 300);
            }
        };
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
        
        // Показываем спиннер
        const preview = document.getElementById(`preview_${fieldName}`);
        if (preview && isLoading) {
            const spinner = document.createElement('div');
            spinner.className = 'spinner-border spinner-border-sm text-primary ms-2';
            spinner.id = `spinner_${fieldName}`;
            preview.appendChild(spinner);
        } else if (preview) {
            const spinner = document.getElementById(`spinner_${fieldName}`);
            if (spinner) spinner.remove();
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
    const objectId = document.querySelector('#control-form')?.dataset?.objectId || null;
    const namespace = document.querySelector('#control-form')?.dataset?.namespace || 'kt08_9a';
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