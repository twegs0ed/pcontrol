// pcontrol/static/pcontrol/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    
    // ===== ЭЛЕМЕНТЫ =====
    const serialInput = document.getElementById('serial_number');
    const searchForm = document.getElementById('search-form');
    const searchBtn = document.getElementById('searchBtn');
    const cameraBtn = document.getElementById('cameraBtn');
    const cameraInput = document.getElementById('cameraInput');
    const resultDiv = document.getElementById('search-result');
    const examples = document.querySelectorAll('.example-badge');
    
    // ===== АВТОФОКУС =====
    if (serialInput) {
        serialInput.focus();
    }
    
    // ===== AJAX ПРОВЕРКА ПРИ ВВОДЕ =====
    let typingTimer = null;
    const doneTypingInterval = 500;
    let isChecking = false;
    
    if (serialInput) {
        serialInput.addEventListener('keyup', function() {
            clearTimeout(typingTimer);
            
            const value = this.value.trim();
            
            if (value.length >= 3) {
                typingTimer = setTimeout(function() {
                    checkSerialAjax(value);
                }, doneTypingInterval);
            } else {
                hideResult();
                if (searchBtn) searchBtn.disabled = true;
            }
        });
    }
    
    // ===== AJAX ПРОВЕРКА =====
    function checkSerialAjax(serial) {
        if (isChecking) return;
        if (!serial || serial.length < 3) return;
        
        isChecking = true;
        
        showResult('info', '<i class="fas fa-spinner fa-spin"></i> Проверка...');
        if (searchBtn) searchBtn.disabled = true;
        
        // ИСПРАВЛЕННЫЙ URL - используем полный путь
        const url = '/pcontrol/check-serial-ajax/?serial=' + encodeURIComponent(serial);
        
        console.log('AJAX запрос к:', url);
        
        fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('HTTP ошибка: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log('Ответ сервера:', data);
            
            // ===== ПРОВЕРКА НА ОШИБКУ =====
            if (data.success === false) {
                showResult('error', `<i class="fas fa-times-circle"></i> ${data.error || 'Ошибка проверки'}`);
                serialInput.classList.remove('is-valid');
                serialInput.classList.add('is-invalid');
                if (searchBtn) searchBtn.disabled = true;
                return;
            }
            
            // ===== ОБЪЕКТ НАЙДЕН =====
            if (data.found === true) {
                const productName = data.category_name || data.product || 'Изделие';
                
                // ===== ОБЪЕКТ ЗАВЕРШЕН =====
                if (data.is_completed === true) {
                    const statusText = data.status === 'completed' ? 'Завершен' : 'Закрыт';
                    showResult('error', 
                        `<i class="fas fa-check-circle text-success"></i> 
                        <strong>Объект ${statusText}</strong><br>
                        Объект <strong>${productName}</strong> с серийным номером <strong>${serial}</strong><br>
                        уже завершен и не доступен для редактирования.<br>
                        <small class="text-muted">Доступ только для просмотра.</small>`
                    );
                    serialInput.classList.remove('is-valid');
                    serialInput.classList.add('is-invalid');
                    if (searchBtn) searchBtn.disabled = true;
                    return;
                }
                
                // ===== ОБЪЕКТ ПРИНАДЛЕЖИТ ТЕКУЩЕМУ ПОЛЬЗОВАТЕЛЮ =====
                if (data.can_edit === true) {
                    showResult('success', 
                        `<i class="fas fa-check-circle"></i> 
                        Найдено: <strong>${productName}</strong>
                        ${data.owner ? `<br><small>Владелец: ${data.owner}</small>` : ''}
                        ${data.progress ? `<br><small>Прогресс: ${data.progress}%</small>` : ''}
                        <div class="result-action mt-2">
                            <small class="d-block text-muted">Нажмите "Поиск" для перехода к редактированию</small>
                        </div>`
                    );
                    serialInput.classList.remove('is-invalid');
                    serialInput.classList.add('is-valid');
                    if (searchBtn) searchBtn.disabled = false;
                    return;
                }
                
                // ===== ОБЪЕКТ ЗАНЯТ ДРУГИМ КОНТРОЛЕРОМ =====
                if (data.blocked === true) {
                    showResult('error', 
                        `<i class="fas fa-lock"></i> 
                        <strong>ДОСТУП ЗАПРЕЩЕН!</strong><br>
                        Объект <strong>${productName}</strong> с серийным номером <strong>${serial}</strong><br>
                        уже проверяется контролером <strong>${data.owner_name || 'Неизвестный контролер'}</strong>.<br>
                        <small class="text-muted">Вы не можете редактировать этот объект.</small>`
                    );
                    serialInput.classList.remove('is-valid');
                    serialInput.classList.add('is-invalid');
                    if (searchBtn) searchBtn.disabled = true;
                    return;
                }
                
                // ===== ОБЪЕКТ ПРИНАДЛЕЖИТ ДРУГОМУ ПОЛЬЗОВАТЕЛЮ =====
                if (data.owner && data.can_edit === false) {
                    showResult('warning',
                        `<i class="fas fa-info-circle"></i> 
                        Объект <strong>${productName}</strong> с серийным номером <strong>${serial}</strong> найден.<br>
                        <small>Владелец: <strong>${data.owner}</strong></small><br>
                        <small class="text-muted">У вас нет прав на редактирование этого объекта.</small>`
                    );
                    serialInput.classList.remove('is-valid');
                    serialInput.classList.add('is-invalid');
                    if (searchBtn) searchBtn.disabled = true;
                    return;
                }
                
            } else {
                // ===== ОБЪЕКТ НЕ НАЙДЕН =====
                const productName = data.category_name || data.product || 'Изделие';
                showResult('warning',
                    `<i class="fas fa-exclamation-triangle"></i> 
                    Объект с серийным номером <strong>${serial}</strong> не найден.<br>
                    <small class="text-muted">Будет создан новый объект "${productName}" при нажатии "Поиск"</small>`
                );
                serialInput.classList.remove('is-valid', 'is-invalid');
                if (searchBtn) searchBtn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showResult('error', '<i class="fas fa-times-circle"></i> Ошибка соединения с сервером');
            if (searchBtn) searchBtn.disabled = false;
            serialInput.classList.remove('is-valid');
            serialInput.classList.add('is-invalid');
        })
        .finally(() => {
            isChecking = false;
        });
    }
    
    // ===== ОТОБРАЖЕНИЕ РЕЗУЛЬТАТА =====
    function showResult(type, html) {
        if (!resultDiv) return;
        resultDiv.className = 'search-result show ' + type;
        resultDiv.innerHTML = html;
        resultDiv.style.display = 'block';
    }
    
    function hideResult() {
        if (!resultDiv) return;
        resultDiv.className = 'search-result';
        resultDiv.innerHTML = '';
        resultDiv.style.display = 'none';
        if (serialInput) {
            serialInput.classList.remove('is-valid', 'is-invalid');
        }
        if (searchBtn) searchBtn.disabled = true;
        isChecking = false;
    }
    
    // ===== ОБРАБОТКА ПРИМЕРОВ =====
    examples.forEach(badge => {
        badge.addEventListener('click', function() {
            if (serialInput) {
                const serial = this.dataset.serial;
                serialInput.value = serial;
                serialInput.focus();
                isChecking = false;
                setTimeout(() => {
                    checkSerialAjax(serial);
                }, 300);
            }
        });
    });
    
    // ===== КАМЕРА =====
    if (cameraBtn) {
        cameraBtn.addEventListener('click', function(e) {
            if (e.target.tagName !== 'INPUT') {
                if (cameraInput) cameraInput.click();
            }
        });
    }
    
    if (cameraInput) {
        cameraInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                cameraBtn.classList.add('scanning');
                const icon = cameraBtn.querySelector('.camera-icon');
                if (icon) icon.style.display = 'none';
                
                // ИСПРАВЛЕННЫЙ URL для сканирования
                const formData = new FormData();
                formData.append('scan_image', file);
                
                fetch('/scan-serial/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    credentials: 'same-origin',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.serial_number) {
                        serialInput.value = data.serial_number;
                        if (data.category_name) {
                            showResult('info', 
                                `<i class="fas fa-check-circle text-success"></i> 
                                Распознан номер: <strong>${data.serial_number}</strong><br>
                                <small>Категория: ${data.category_name}</small>`
                            );
                        } else {
                            showResult('info', 
                                `<i class="fas fa-check-circle text-success"></i> 
                                Распознан номер: <strong>${data.serial_number}</strong>`
                            );
                        }
                        serialInput.focus();
                        isChecking = false;
                        setTimeout(() => {
                            checkSerialAjax(data.serial_number);
                        }, 500);
                    } else {
                        showResult('error', 
                            `<i class="fas fa-times-circle"></i> 
                            ${data.error || 'Не удалось распознать номер'}<br>
                            <small class="text-muted">Введите номер вручную</small>`
                        );
                        serialInput.focus();
                    }
                })
                .catch(error => {
                    console.error('Ошибка сканирования:', error);
                    showResult('error', 
                        `<i class="fas fa-times-circle"></i> 
                        Ошибка при сканировании.<br>
                        <small class="text-muted">Попробуйте ввести номер вручную</small>`
                    );
                })
                .finally(() => {
                    cameraBtn.classList.remove('scanning');
                    if (icon) icon.style.display = 'inline';
                    this.value = '';
                });
            }
        });
    }
    
    // ===== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ =====
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
    
    // ===== ОТПРАВКА ФОРМЫ =====
    if (serialInput) {
        serialInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (searchBtn && !searchBtn.disabled) {
                    searchBtn.click();
                }
            }
        });
    }
    
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const value = serialInput ? serialInput.value.trim() : '';
            if (!value || value.length < 3) {
                e.preventDefault();
                showResult('error', '<i class="fas fa-exclamation-circle"></i> Введите серийный номер');
                return;
            }
            
            if (searchBtn && searchBtn.disabled) {
                e.preventDefault();
                return;
            }
            
            if (searchBtn) {
                searchBtn.disabled = true;
                searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Поиск...';
            }
        });
    }
    
});