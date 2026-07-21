
document.addEventListener('DOMContentLoaded', function() {
    
    // Инициализация предпросмотра для всех изображений
    for (var i = 1; i <= 7; i++) {
        var imageInput = document.querySelector('#id_image' + i);
        if (imageInput) {
            imageInput.addEventListener('change', function() {
                var fieldName = this.id.replace('id_', '');
                previewImage(this, 'preview_' + fieldName, 'current_' + fieldName, 'no_' + fieldName);
            });
        }
    }
    
    // Сканирование
    var scanInput = document.getElementById('scanFileInput');
    var scanBtn = document.getElementById('scanSendBtn');
    var scanStatus = document.getElementById('scanStatus');
    var serialInput = document.querySelector('#id_serial_number');
    var enterBtn = document.getElementById('enterBtn');
    var hiddenField = document.getElementById('scanned_photo_base64');
    
    
    // Функция сканирования
    function scanSend() {
        if (!scanInput) {
            console.error('scanInput не найден!');
            return;
        }
        
        var file = scanInput.files[0];
        if (!file) {
            if (scanStatus) {
                scanStatus.style.display = 'block';
                scanStatus.innerHTML = '<div class="alert alert-warning">Сначала выберите изображение</div>';
            }
            return;
        }
        
        var formData = new FormData();
        formData.append('scan_image', file);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        
        if (scanStatus) {
            scanStatus.style.display = 'block';
            scanStatus.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin"></i> Распознавание серийного номера...</div>';
        }
        
        var scanUrl = '/gs14/scan-serial/';
        
        fetch(scanUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(function(response) {
            if (!response.ok) {
                return response.json().then(function(data) {
                    throw new Error(JSON.stringify(data));
                });
            }
            return response.json();
        })
        .then(function(data) {
            var html = '';
            
            // ===== Сохраняем фото в скрытое поле =====
            if (data.photo_base64) {
                
                if (hiddenField) {
                    hiddenField.value = 'data:image/jpeg;base64,' + data.photo_base64;
                } else {
                    console.error('❌ hiddenField не найден!');
                    var form = document.getElementById('control-form');
                    if (form) {
                        var newHidden = document.createElement('input');
                        newHidden.type = 'hidden';
                        newHidden.id = 'scanned_photo_base64';
                        newHidden.name = 'scanned_photo_base64';
                        newHidden.value = 'data:image/jpeg;base64,' + data.photo_base64;
                        form.appendChild(newHidden);
                        hiddenField = newHidden;
                    }
                }
            } else {
                console.warn('⚠️ photo_base64 не получен от сервера');
            }
            
            if (data.success && data.serial_number) {
                // Подставляем распознанный номер
                if (serialInput) {
                    serialInput.value = data.serial_number;
                    serialInput.style.borderColor = '#28a745';
                    serialInput.style.backgroundColor = '#f0fff0';
                }
                
                // Показываем превью
                if (data.photo_base64 && data.photo_base64.length > 100) {
                    var container = document.getElementById('serial-photo-container');
                    if (container) {
                        var oldPreviews = container.querySelectorAll('.scan-preview');
                        oldPreviews.forEach(function(el) { el.remove(); });
                        
                        var img = document.createElement('img');
                        img.className = 'scan-preview';
                        img.src = 'data:image/jpeg;base64,' + data.photo_base64;
                        img.style.cssText = 'max-width: 150px; max-height: 150px; border-radius: 6px; object-fit: cover; border: 2px solid #28a745; padding: 3px; margin-top: 10px;';
                        container.appendChild(img);
                        
                        var noImg = document.getElementById('no_serial_photo');
                        if (noImg) noImg.style.display = 'none';
                    }
                }
                
                // ===== УБИРАЕМ ПРОВЕРКУ НА exists =====
                // Просто показываем сообщение об успешном распознавании
                html = '<div class="alert alert-success">' +
                    '<i class="fas fa-check-circle"></i> ' +
                    'Распознан номер: <strong>' + data.serial_number + '</strong>' +
                '</div>';
                html += '<div class="alert alert-info mt-2">' +
                    '<i class="fas fa-info-circle"></i> ' +
                    'Проверьте номер и нажмите кнопку "Создать" для сохранения объекта с фото.' +
                '</div>';
                
                if (enterBtn) {
                    enterBtn.style.backgroundColor = '#28a745';
                    enterBtn.style.borderColor = '#28a745';
                    enterBtn.innerHTML = '<i class="fas fa-arrow-right"></i> Ввод ✓';
                }
                
            } else {
                // Ошибка
                var errorMsg = data.error || 'Не удалось распознать серийный номер';
                html = '<div class="alert alert-danger">' +
                    '<i class="fas fa-times-circle"></i> ' + errorMsg +
                '</div>';
                html += '<div class="alert alert-warning mt-2">💡 Попробуйте:</div>';
                html += '<ul class="text-muted">' +
                    '<li>Сделать фото более четким</li>' +
                    '<li>Обеспечить хорошее освещение</li>' +
                    '<li>Расположить номер в центре кадра</li>' +
                    '<li>Использовать контрастный фон</li>' +
                '</ul>';
                
                // Если фото есть, но номер не распознан - все равно показываем фото
                if (data.photo_base64 && data.photo_base64.length > 100) {
                    html += '<div class="alert alert-info mt-2">📸 Фото загружено. Введите номер вручную.</div>';
                    var container = document.getElementById('serial-photo-container');
                    if (container) {
                        var oldPreviews = container.querySelectorAll('.scan-preview');
                        oldPreviews.forEach(function(el) { el.remove(); });
                        
                        var img = document.createElement('img');
                        img.className = 'scan-preview';
                        img.src = 'data:image/jpeg;base64,' + data.photo_base64;
                        img.style.cssText = 'max-width: 150px; max-height: 150px; border-radius: 6px; object-fit: cover; border: 2px solid #ffc107; padding: 3px; margin-top: 10px;';
                        container.appendChild(img);
                        
                        var noImg = document.getElementById('no_serial_photo');
                        if (noImg) noImg.style.display = 'none';
                    }
                }
                
                if (serialInput) {
                    serialInput.value = '';
                    serialInput.style.borderColor = '#dc3545';
                    serialInput.style.backgroundColor = '#fff0f0';
                    serialInput.focus();
                }
            }
            
            if (scanStatus) {
                scanStatus.innerHTML = html;
            }
        })
        .catch(function(error) {
            console.error('Ошибка:', error);
            var errorMsg = 'Ошибка при сканировании';
            try {
                var errorData = JSON.parse(error.message);
                errorMsg = errorData.error || errorData.message || errorMsg;
            } catch (e) {
                errorMsg = error.message || errorMsg;
            }
            if (scanStatus) {
                scanStatus.innerHTML = '<div class="alert alert-danger">❌ ' + errorMsg + '</div>';
            }
        });
    }
    
    // Привязываем обработчики
    if (scanBtn) {
        scanBtn.onclick = scanSend;
    }
    
    if (scanInput) {
        scanInput.onchange = function() {
            if (this.files[0]) {
                this.style.borderColor = '#17a2b8';
                this.style.backgroundColor = '#f0f8ff';
                setTimeout(scanSend, 300);
            }
        };
    }
    
    if (serialInput) {
        serialInput.oninput = function() {
            this.style.borderColor = '';
            this.style.backgroundColor = '';
            if (enterBtn) {
                enterBtn.style.backgroundColor = '';
                enterBtn.style.borderColor = '';
                enterBtn.innerHTML = '<i class="fas fa-arrow-right"></i> Ввод';
            }
        };
    }
    
});

// Функция предпросмотра изображения
function previewImage(input, previewId, currentImgId, noImgId) {
    var preview = document.getElementById(previewId);
    if (!preview) return;
    
    var file = input.files[0];
    if (file) {
        var reader = new FileReader();
        reader.onload = function(e) {
            var img = preview.querySelector('img');
            if (img) {
                img.src = e.target.result;
            }
            preview.style.display = 'block';
            
            if (currentImgId) {
                var currentImg = document.getElementById(currentImgId);
                if (currentImg) currentImg.style.display = 'none';
            }
            if (noImgId) {
                var noImg = document.getElementById(noImgId);
                if (noImg) noImg.style.display = 'none';
            }
        };
        reader.readAsDataURL(file);
    } else {
        preview.style.display = 'none';
        if (currentImgId) {
            var currentImg = document.getElementById(currentImgId);
            if (currentImg) currentImg.style.display = '';
        }
        if (noImgId) {
            var noImg = document.getElementById(noImgId);
            if (noImg) noImg.style.display = '';
        }
    }
}


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
        
        scanStatus.style.display = 'block';
        scanStatus.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin"></i> Распознавание серийного номера...</div>';
        
        const scanUrl = `/${this.namespace}/scan-serial/`;
        
        fetch(scanUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(JSON.stringify(data));
                });
            }
            return response.json();
        })
        .then(data => {
            const serialInput = document.querySelector('#id_serial_number');
            const hiddenField = document.getElementById('scanned_photo_base64');
            let html = '';
            
            if (data.success && data.serial_number) {
                // Подставляем распознанный номер в поле
                if (serialInput) {
                    serialInput.value = data.serial_number;
                    serialInput.style.borderColor = '#28a745';
                    serialInput.style.backgroundColor = '#f0fff0';
                }
                
                // СОХРАНЯЕМ ФОТО В СКРЫТОЕ ПОЛЕ
                if (hiddenField && data.photo_base64) {
                    // Проверяем, что данные не пустые
                    if (data.photo_base64.length > 100) {
                        // Добавляем префикс для base64 изображения
                        hiddenField.value = `data:image/jpeg;base64,${data.photo_base64}`;
                        
                        // Проверяем, что поле действительно заполнилось
                        if (hiddenField.value.length > 100) {
                        } else {
                        }
                    } else {
                        console.warn('⚠️ Фото слишком маленькое:', data.photo_base64.length);
                    }
                } else {
                    console.warn('⚠️ Нет данных для сохранения фото');
                    console.warn('hiddenField:', hiddenField);
                    console.warn('data.photo_base64:', data.photo_base64 ? data.photo_base64.substring(0, 50) : 'EMPTY');
                }
                
                // Показываем превью фото
                if (data.photo_base64 && data.photo_base64.length > 100) {
                    this.showScanPreviewFromBase64(data.photo_base64);
                }
                
                // Показываем сообщение
                let existsMsg = data.exists ? ' ⚠️ Этот номер уже существует в базе!' : '';
                html = `<div class="alert alert-success">
                    <i class="fas fa-check-circle"></i> 
                    Распознан номер: <strong>${data.serial_number}</strong>${existsMsg}
                </div>`;
                html += `<div class="alert alert-info mt-2">
                    <i class="fas fa-info-circle"></i> 
                    Проверьте номер и нажмите кнопку "Создать" для сохранения объекта с фото.
                </div>`;
                
                if (data.exists) {
                    html += `<div class="alert alert-warning mt-2">
                        <i class="fas fa-exclamation-triangle"></i> 
                        Внимание! Объект с таким номером уже существует. 
                        <a href="/${this.namespace}/edit/${data.serial_number}/">Перейти к редактированию</a>
                    </div>`;
                }
                
                scanStatus.innerHTML = html;
                
            } else {
                // Ошибка распознавания
                let errorMsg = data.error || 'Не удалось распознать серийный номер';
                html = `<div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i> ${errorMsg}
                </div>`;
                html += `<div class="alert alert-warning mt-2">💡 Попробуйте:</div>`;
                html += `<ul class="text-muted">
                    <li>Сделать фото более четким</li>
                    <li>Обеспечить хорошее освещение</li>
                    <li>Расположить номер в центре кадра</li>
                    <li>Использовать контрастный фон</li>
                </ul>`;
                
                scanStatus.innerHTML = html;
            }
        })
        .catch(error => {
            console.error('Ошибка сканирования:', error);
            scanStatus.innerHTML = `<div class="alert alert-danger">❌ Ошибка: ${error.message}</div>`;
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

// Показать превью из base64
showScanPreviewFromBase64(base64Data) {
    const container = document.getElementById('serial-photo-container');
    if (!container) return;
    
    // Удаляем старые превью
    const oldPreviews = container.querySelectorAll('.scan-preview');
    oldPreviews.forEach(el => el.remove());
    
    // Создаем новое изображение
    const img = document.createElement('img');
    img.className = 'scan-preview';
    img.src = `data:image/jpeg;base64,${base64Data}`;
    img.style.cssText = 'max-width: 150px; max-height: 150px; border-radius: 6px; object-fit: cover; border: 2px solid #28a745; padding: 3px; margin-top: 10px;';
    container.appendChild(img);
    
    // Скрываем "Нет изображения"
    const noImg = document.getElementById('no_serial_photo');
    if (noImg) noImg.style.display = 'none';
}

// Показать превью из base64
showScanPreviewFromBase64(base64Data) {
    const container = document.getElementById('serial-photo-container');
    if (!container) return;
    
    // Удаляем старые превью
    const oldPreviews = container.querySelectorAll('.scan-preview');
    oldPreviews.forEach(el => el.remove());
    
    // Создаем новое изображение
    const img = document.createElement('img');
    img.className = 'scan-preview';
    img.src = `data:image/jpeg;base64,${base64Data}`;
    img.style.cssText = 'max-width: 150px; max-height: 150px; border-radius: 6px; object-fit: cover; border: 2px solid #28a745; padding: 3px; margin-top: 10px;';
    container.appendChild(img);
    
    // Скрываем "Нет изображения"
    const noImg = document.getElementById('no_serial_photo');
    if (noImg) noImg.style.display = 'none';
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