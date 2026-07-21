// unified_products/static/unified_products/js/product_form.js

document.addEventListener('DOMContentLoaded', function() {
    
    console.log('product_form.js загружен');
    
    // ===== ЭЛЕМЕНТЫ =====
    const serialInput = document.getElementById('id_serial_number');
    const categorySelect = document.getElementById('id_category');
    const categoryDetectResult = document.getElementById('categoryDetectResult');
    const detectedCategoryName = document.getElementById('detectedCategoryName');
    const imagesGrid = document.getElementById('imagesGrid');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const scanBtn = document.getElementById('scanSerialBtn');
    const form = document.getElementById('productForm');
    const scannedPhotoInput = document.getElementById('scanned_photo_base64');
    
    // ===== ДАННЫЕ КАТЕГОРИЙ =====
    const categories = window.categoriesData || [];
    console.log('Категории для определения:', categories);
    
    // ===== ФУНКЦИЯ ПОЛУЧЕНИЯ CSRF TOKEN =====
    function getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // ===== ФУНКЦИЯ ОПРЕДЕЛЕНИЯ КАТЕГОРИИ =====
    function detectCategory(serial) {
        console.log('detectCategory вызван с:', serial);
        
        if (!serial || serial.length < 3) {
            if (categoryDetectResult) {
                categoryDetectResult.style.display = 'none';
            }
            if (serialInput) {
                serialInput.classList.remove('is-valid', 'is-invalid');
            }
            return null;
        }
        
        let matchedCategory = null;
        for (let cat of categories) {
            if (serial.startsWith(cat.prefix)) {
                matchedCategory = cat;
                break;
            }
        }
        
        console.log('Найдена категория:', matchedCategory);
        
        if (matchedCategory && categoryDetectResult && detectedCategoryName) {
            detectedCategoryName.textContent = matchedCategory.name;
            categoryDetectResult.style.display = 'block';
            categoryDetectResult.querySelector('.alert').className = 'alert alert-info';
            
            if (categorySelect) {
                categorySelect.value = matchedCategory.id;
                if (window.isCreate) {
                    categorySelect.disabled = true;
                }
            }
            
            if (serialInput) {
                serialInput.classList.remove('is-invalid');
                serialInput.classList.add('is-valid');
            }
            
            return matchedCategory;
        } else if (categoryDetectResult && detectedCategoryName) {
            categoryDetectResult.style.display = 'block';
            categoryDetectResult.querySelector('.alert').className = 'alert alert-warning';
            detectedCategoryName.textContent = 'Категория не найдена (создайте категорию с соответствующим префиксом)';
            
            if (categorySelect) {
                categorySelect.value = '';
                categorySelect.disabled = false;
            }
            
            if (serialInput) {
                serialInput.classList.remove('is-valid');
                serialInput.classList.add('is-invalid');
            }
            
            return null;
        }
        return null;
    }
    
    // ===== ОБРАБОТЧИК ВВОДА СЕРИЙНОГО НОМЕРА =====
    if (serialInput) {
        serialInput.addEventListener('input', function() {
            const serial = this.value.trim();
            detectCategory(serial);
        });
        
        if (serialInput.value.trim()) {
            setTimeout(function() {
                detectCategory(serialInput.value.trim());
            }, 100);
        }
    }
    
    // ===== ЗАГРУЗКА ИЗОБРАЖЕНИЯ =====
    function uploadImage(productId, fieldIndex, fileInput) {
        console.log('uploadImage вызван:', productId, fieldIndex);
        
        if (!productId) {
            console.error('productId не передан!');
            showToast('error', 'Ошибка: ID продукта не найден');
            return;
        }
        
        const file = fileInput.files[0];
        if (!file) {
            console.log('Файл не выбран');
            return;
        }
        
        console.log('Файл:', file.name, file.type, file.size);
        
        if (!file.type.startsWith('image/')) {
            showToast('error', 'Пожалуйста, выберите изображение');
            fileInput.value = '';
            return;
        }
        
        if (file.size > 10 * 1024 * 1024) {
            showToast('error', 'Файл слишком большой (максимум 10MB)');
            fileInput.value = '';
            return;
        }
        
        const card = fileInput.closest('.image-card');
        if (!card) {
            console.log('Карточка не найдена');
            return;
        }
        
        const formData = new FormData();
        formData.append('image', file);
        
        card.classList.add('uploading', 'loading');
        const progress = card.querySelector('.upload-progress .progress-bar');
        if (progress) {
            progress.style.width = '0%';
        }
        
        const url = '/unified-products/ajax/save-image/' + productId + '/' + fieldIndex + '/';
        console.log('Отправка запроса на:', url);
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin',
            body: formData
        })
        .then(response => {
            console.log('Ответ получен, статус:', response.status);
            if (!response.ok) {
                throw new Error('HTTP ошибка: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log('Данные ответа:', data);
            if (data.success) {
                updateImageCard(card, data);
                updateProgress(data);
                showToast('success', 'Изображение загружено!');
                
                if (data.is_completed && data.redirect_url) {
                    setTimeout(function() {
                        showToast('success', '✅ Все фото загружены! Перенаправление...');
                        setTimeout(function() {
                            window.location.href = data.redirect_url;
                        }, 2000);
                    }, 500);
                }
            } else {
                console.log('Ошибка от сервера:', data.error);
                showToast('error', data.error || 'Ошибка загрузки');
                card.classList.remove('uploading', 'loading');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showToast('error', 'Ошибка соединения с сервером: ' + error.message);
            card.classList.remove('uploading', 'loading');
        })
        .finally(() => {
            fileInput.value = '';
        });
    }
    
    // ===== ОБНОВЛЕНИЕ КАРТОЧКИ =====
    function updateImageCard(card, data) {
        console.log('updateImageCard вызван');
        if (!card) return;
        
        const statusBadge = card.querySelector('.status-badge');
        const preview = card.querySelector('.image-preview');
        const placeholder = card.querySelector('.placeholder');
        const uploadBtn = card.querySelector('.upload-btn');
        const deleteBtn = card.querySelector('.delete-btn');
        
        if (data.image_url) {
            card.classList.add('has-image');
            card.classList.remove('uploading', 'loading');
            
            if (statusBadge) {
                statusBadge.textContent = 'Загружено';
                statusBadge.className = 'status-badge badge bg-success';
            }
            
            if (preview) {
                preview.src = data.image_url + '?t=' + Date.now();
                preview.style.display = 'block';
            }
            
            if (placeholder) {
                placeholder.style.display = 'none';
            }
            
            if (uploadBtn) {
                uploadBtn.innerHTML = '<i class="fas fa-sync"></i> Заменить';
            }
            
            if (deleteBtn) {
                deleteBtn.style.display = 'block';
            }
        }
    }
    
    // ===== ОБНОВЛЕНИЕ ПРОГРЕССА =====
    function updateProgress(data) {
        console.log('updateProgress вызван', data);
        if (!data) return;
        
        if (data.filled !== undefined && data.total !== undefined) {
            const filled = parseInt(data.filled) || 0;
            const total = parseInt(data.total) || 1;
            const progress = Math.round((filled / total) * 100);
            
            if (progressBar) {
                progressBar.style.width = progress + '%';
                progressBar.textContent = progress + '%';
                progressBar.setAttribute('aria-valuenow', progress);
                
                if (progress === 100) {
                    progressBar.className = 'progress-bar bg-success';
                } else {
                    progressBar.className = 'progress-bar bg-warning';
                }
            }
            
            if (progressText) {
                progressText.textContent = filled + '/' + total;
            }
        }
    }
    
    // ===== УДАЛЕНИЕ ИЗОБРАЖЕНИЯ =====
    window.deleteImage = function(productId, fieldIndex) {
        console.log('deleteImage вызван:', productId, fieldIndex);
        
        if (!productId) {
            console.error('productId не передан!');
            showToast('error', 'Ошибка: ID продукта не найден');
            return;
        }
        
        if (!confirm('Удалить это изображение?')) return;
        
        const card = document.querySelector('.image-card[data-field="' + fieldIndex + '"]');
        if (!card) return;
        
        card.classList.add('loading');
        
        const url = '/unified-products/ajax/delete-image/' + productId + '/' + fieldIndex + '/';
        console.log('Удаление по URL:', url);
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Ответ удаления:', data);
            if (data.success) {
                resetImageCard(card);
                if (data.progress !== undefined) {
                    updateProgress(data);
                }
                showToast('success', 'Изображение удалено');
            } else {
                showToast('error', data.error || 'Ошибка удаления');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showToast('error', 'Ошибка соединения с сервером');
        })
        .finally(() => {
            card.classList.remove('loading');
        });
    };
    
    // ===== СБРОС КАРТОЧКИ =====
    function resetImageCard(card) {
        card.classList.remove('has-image', 'uploading', 'loading');
        
        const statusBadge = card.querySelector('.status-badge');
        const preview = card.querySelector('.image-preview');
        const placeholder = card.querySelector('.placeholder');
        const deleteBtn = card.querySelector('.delete-btn');
        const uploadBtn = card.querySelector('.upload-btn');
        
        if (statusBadge) {
            statusBadge.textContent = 'Пусто';
            statusBadge.className = 'status-badge badge bg-secondary';
        }
        
        if (preview) {
            preview.src = '';
            preview.style.display = 'none';
        }
        
        if (placeholder) {
            placeholder.style.display = 'block';
        }
        
        if (deleteBtn) {
            deleteBtn.style.display = 'none';
        }
        
        if (uploadBtn) {
            uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Загрузить';
        }
    }
    
    // ===== СОХРАНЕНИЕ ЗАГОЛОВКА =====
    window.saveTitle = function(productId, fieldIndex, input) {
        console.log('saveTitle вызван:', productId, fieldIndex);
        
        if (!productId) {
            console.warn('productId не передан, заголовок не сохранен');
            return;
        }
        
        const value = input.value.trim();
        
        fetch('/unified-products/ajax/save-title/' + productId + '/' + fieldIndex + '/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin',
            body: JSON.stringify({ value: value })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Ответ сохранения заголовка:', data);
            if (data.success) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
                setTimeout(function() {
                    input.classList.remove('is-valid');
                }, 2000);
            } else {
                input.classList.add('is-invalid');
            }
        })
        .catch(error => {
            console.error('Ошибка сохранения заголовка:', error);
            input.classList.add('is-invalid');
        });
    };
    
    // ===== ПОДКЛЮЧАЕМ ОБРАБОТЧИКИ ДЛЯ ФАЙЛОВЫХ ИНПУТОВ =====
    document.querySelectorAll('.image-card .file-input-wrapper input[type="file"]').forEach(function(input) {
        console.log('Найден input файла');
        
        input.addEventListener('change', function() {
            console.log('Изменение файла в input');
            
            const card = this.closest('.image-card');
            if (!card) {
                console.log('Карточка не найдена');
                return;
            }
            
            const fieldIndex = card.dataset.field;
            const productId = window.productId;
            
            console.log('productId:', productId, 'fieldIndex:', fieldIndex);
            
            if (productId) {
                uploadImage(productId, fieldIndex, this);
            } else {
                // Режим создания
                const file = this.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const hiddenInput = document.getElementById('temp_image_' + fieldIndex);
                        if (hiddenInput) {
                            hiddenInput.value = e.target.result;
                            card.classList.add('has-image');
                            const placeholder = card.querySelector('.placeholder');
                            if (placeholder) placeholder.style.display = 'none';
                            const preview = card.querySelector('.image-preview');
                            if (preview) {
                                preview.src = e.target.result;
                                preview.style.display = 'block';
                            }
                            showToast('success', 'Изображение выбрано');
                        }
                    };
                    reader.readAsDataURL(file);
                }
            }
        });
    });
    
    // ===== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ТОСТОВ =====
    function showToast(type, message) {
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
            document.body.appendChild(toastContainer);
        }
        
        const colors = {
            success: '#d4edda',
            error: '#f8d7da',
            warning: '#fff3cd',
            info: '#d1ecf1'
        };
        
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        
        const toast = document.createElement('div');
        toast.className = 'toast show';
        toast.style.cssText = `
            min-width: 250px;
            background: ${colors[type] || '#fff'};
            border-radius: 8px;
            padding: 12px 20px;
            margin-bottom: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: fadeIn 0.3s ease;
            border-left: 4px solid ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : type === 'warning' ? '#ffc107' : '#17a2b8'};
        `;
        toast.innerHTML = `
            <i class="fas ${icons[type] || 'fa-info-circle'} me-2"></i>
            ${message}
        `;
        
        toastContainer.appendChild(toast);
        
        setTimeout(function() {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.5s';
            setTimeout(function() {
                toast.remove();
            }, 500);
        }, 4000);
    }
    
    console.log('product_form.js инициализирован');



    









    if (scanBtn && serialInput) {
    console.log('Кнопка сканирования найдена');
    
    scanBtn.addEventListener('click', function(e) {
        e.preventDefault();
        console.log('Нажата кнопка сканирования');
        
        // Создаем скрытый input для файла
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.capture = 'environment';
        fileInput.style.display = 'none';
        document.body.appendChild(fileInput);
        
        fileInput.click();
        
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (!file) {
                console.log('Файл не выбран');
                fileInput.remove();
                return;
            }
            
            console.log('Файл выбран:', file.name, file.size, file.type);
            
            // Проверка типа файла
            if (!file.type.startsWith('image/')) {
                showToast('error', 'Пожалуйста, выберите изображение');
                fileInput.remove();
                return;
            }
            
            const formData = new FormData();
            formData.append('scan_image', file);
            
            // Показываем индикатор загрузки
            scanBtn.classList.add('scanning');
            scanBtn.disabled = true;
            scanBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Распознавание...';
            
            console.log('Отправка запроса на /unified-products/scan-serial/');
            console.log('FormData:', formData);
            
            // Отправляем на сервер
            fetch('/unified-products/scan-serial/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
                body: formData
            })
            .then(response => {
                console.log('Ответ получен, статус:', response.status);
                console.log('Ответ headers:', response.headers);
                
                if (!response.ok) {
                    // Пытаемся получить текст ошибки
                    return response.text().then(text => {
                        console.error('Текст ошибки:', text);
                        throw new Error('HTTP ошибка: ' + response.status + ' - ' + text);
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Данные ответа:', data);
                
                if (data.success && data.serial_number) {
                    // Устанавливаем серийный номер
                    serialInput.value = data.serial_number;
                    
                    // Сохраняем фото в скрытое поле
                    if (data.photo_base64 && scannedPhotoInput) {
                        scannedPhotoInput.value = data.photo_base64;
                        console.log('Фото сохранено в скрытое поле, длина:', data.photo_base64.length);
                    }
                    
                    // Определяем категорию
                    if (data.category_id) {
                        const categorySelect = document.getElementById('id_category');
                        if (categorySelect) {
                            categorySelect.value = data.category_id;
                            showToast('success', 'Категория определена: ' + data.category_name);
                        }
                    }
                    
                    // Вызываем определение категории
                    if (typeof window.detectCategory === 'function') {
                        window.detectCategory(data.serial_number);
                    } else if (typeof detectCategory === 'function') {
                        detectCategory(data.serial_number);
                    }
                    
                    showToast('success', '✅ Распознан номер: ' + data.serial_number);
                    
                    // Триггерим событие input для обновления
                    serialInput.dispatchEvent(new Event('input'));
                    
                } else {
                    showToast('error', data.error || 'Не удалось распознать номер');
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                showToast('error', 'Ошибка сканирования: ' + error.message);
            })
            .finally(() => {
                // Восстанавливаем кнопку
                scanBtn.classList.remove('scanning');
                scanBtn.disabled = false;
                scanBtn.innerHTML = '<i class="fas fa-camera scan-icon"></i>';
                fileInput.remove();
            });
        });
    });
}









});