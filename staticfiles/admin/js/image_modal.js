// static/admin/js/image_modal.js

// Функция для открытия модального окна
function openImageModal(imageUrl, caption) {
    console.log('openImageModal called', imageUrl, caption);
    
    // Проверяем, существует ли модальное окно
    let modal = document.getElementById('imageModal');
    
    if (!modal) {
        // Создаем модальное окно
        modal = document.createElement('div');
        modal.id = 'imageModal';
        modal.style.cssText = 'display: none; position: fixed; z-index: 999999; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.9);';
        
        modal.innerHTML = `
            <div style="position: relative; margin: auto; padding: 20px; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <span style="position: absolute; top: 20px; right: 35px; color: #fff; font-size: 40px; font-weight: bold; cursor: pointer; z-index: 1000000; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.1); border-radius: 50%; border: 2px solid rgba(255,255,255,0.3); transition: all 0.3s;" 
                      onclick="closeImageModal()"
                      onmouseover="this.style.color='#ff4444'; this.style.background='rgba(255,255,255,0.2)'; this.style.transform='rotate(90deg)';"
                      onmouseout="this.style.color='#fff'; this.style.background='rgba(255,255,255,0.1)'; this.style.transform='rotate(0deg)';">&times;</span>
                <img id="modalImage" style="max-width: 90%; max-height: 85vh; border-radius: 10px; box-shadow: 0 0 50px rgba(0,0,0,0.5); border: 3px solid rgba(255,255,255,0.2); object-fit: contain;" alt="Увеличенное изображение">
                <div id="modalCaption" style="color: #fff; margin-top: 20px; font-size: 18px; background: rgba(0,0,0,0.7); padding: 10px 30px; border-radius: 30px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1);"></div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Закрытие по клику на фон
        modal.addEventListener('click', function(e) {
            if (e.target === modal || e.target === modal.querySelector('div')) {
                closeImageModal();
            }
        });
        
        // Закрытие по клавише ESC
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeImageModal();
            }
        });
    }
    
    // Устанавливаем изображение
    const img = document.getElementById('modalImage');
    const captionEl = document.getElementById('modalCaption');
    
    if (img) {
        img.src = imageUrl;
        img.alt = caption || 'Изображение';
        img.onerror = function() {
            this.src = '';
            this.alt = 'Ошибка загрузки изображения';
        };
    }
    
    if (captionEl) {
        captionEl.textContent = caption || 'Просмотр изображения';
    }
    
    // Показываем модальное окно
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// Функция для закрытия модального окна
function closeImageModal() {
    const modal = document.getElementById('imageModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Добавляем глобальные функции
window.openImageModal = openImageModal;
window.closeImageModal = closeImageModal;

console.log('Image modal loaded');