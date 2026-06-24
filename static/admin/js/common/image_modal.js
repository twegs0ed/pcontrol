// static/admin/js/common/image_modal.js
function openImageModal(imageUrl, title) {
    // Проверяем, существует ли уже модальное окно
    let modal = document.getElementById('imageModal');
    
    if (!modal) {
        // Создаем модальное окно
        modal = document.createElement('div');
        modal.id = 'imageModal';
        modal.style.cssText = `
            display: none;
            position: fixed;
            z-index: 9999;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
            overflow: auto;
            animation: fadeIn 0.3s;
        `;
        
        // Создаем контент модального окна
        const content = document.createElement('div');
        content.style.cssText = `
            position: relative;
            margin: auto;
            padding: 20px;
            max-width: 90%;
            max-height: 90%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
        `;
        
        // Кнопка закрытия
        const closeBtn = document.createElement('span');
        closeBtn.innerHTML = '&times;';
        closeBtn.style.cssText = `
            position: absolute;
            top: 20px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.3s;
            z-index: 10000;
        `;
        closeBtn.onmouseover = function() {
            this.style.color = '#ff0000';
        };
        closeBtn.onmouseout = function() {
            this.style.color = '#f1f1f1';
        };
        closeBtn.onclick = function() {
            closeImageModal();
        };
        
        // Изображение
        const img = document.createElement('img');
        img.id = 'modalImage';
        img.style.cssText = `
            max-width: 90%;
            max-height: 80vh;
            object-fit: contain;
            border-radius: 8px;
            box-shadow: 0 0 30px rgba(0,0,0,0.5);
            margin: auto;
        `;
        
        // Заголовок
        const caption = document.createElement('div');
        caption.id = 'modalCaption';
        caption.style.cssText = `
            margin-top: 20px;
            color: #f1f1f1;
            font-size: 18px;
            text-align: center;
            padding: 10px;
            background: rgba(0,0,0,0.5);
            border-radius: 8px;
            max-width: 80%;
        `;
        
        content.appendChild(closeBtn);
        content.appendChild(img);
        content.appendChild(caption);
        modal.appendChild(content);
        document.body.appendChild(modal);
        
        // Закрытие по клику вне изображения
        modal.onclick = function(event) {
            if (event.target === modal) {
                closeImageModal();
            }
        };
        
        // Закрытие по Escape
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && modal.style.display === 'block') {
                closeImageModal();
            }
        });
    }
    
    // Устанавливаем изображение и заголовок
    const img = document.getElementById('modalImage');
    const caption = document.getElementById('modalCaption');
    img.src = imageUrl;
    caption.textContent = title || 'Изображение';
    
    // Показываем модальное окно
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Добавляем анимацию
    modal.style.animation = 'none';
    modal.offsetHeight; // Trigger reflow
    modal.style.animation = 'fadeIn 0.3s';
}

function closeImageModal() {
    const modal = document.getElementById('imageModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Добавляем CSS анимацию
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
`;
document.head.appendChild(style);