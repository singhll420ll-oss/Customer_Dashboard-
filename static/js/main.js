// Main JavaScript File
document.addEventListener('DOMContentLoaded', function() {
    // Flash messages auto-close
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(flash => {
        const closeBtn = flash.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                flash.style.opacity = '0';
                setTimeout(() => flash.remove(), 300);
            });
        }
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (flash.parentNode) {
                flash.style.opacity = '0';
                setTimeout(() => flash.remove(), 300);
            }
        }, 5000);
    });
    
    // Location detection
    const locationBtns = document.querySelectorAll('.get-location');
    locationBtns.forEach(btn => {
        btn.addEventListener('click', async function() {
            const input = this.closest('.form-group').querySelector('.form-control');
            if (!input) return;
            
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detecting...';
            this.disabled = true;
            
            try {
                const response = await fetch('/api/get_location');
                const data = await response.json();
                
                if (data.success) {
                    input.value = data.location;
                    showNotification('Location detected', 'success');
                } else {
                    showNotification('Failed to detect location', 'error');
                }
            } catch (error) {
                showNotification('Network error', 'error');
            } finally {
                this.innerHTML = '<i class="fas fa-map-marker-alt"></i> Use Current Location';
                this.disabled = false;
            }
        });
    });
    
    // Bottom nav active state
    const navItems = document.querySelectorAll('.nav-item');
    const currentPath = window.location.pathname;
    
    navItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href && (currentPath.includes(href.replace('/', '')) || 
                     (currentPath === '/' && href.includes('dashboard')))) {
            item.classList.add('active');
        }
    });
});

// Notification system
function showNotification(message, type = 'info') {
    const container = document.querySelector('.flash-container') || createNotificationContainer();
    
    const notification = document.createElement('div');
    notification.className = `flash flash-${type}`;
    notification.innerHTML = `
        ${message}
        <button class="flash-close">&times;</button>
    `;
    
    container.appendChild(notification);
    
    // Auto remove
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
    
    // Close button
    notification.querySelector('.flash-close').addEventListener('click', () => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    });
}

function createNotificationContainer() {
    const container = document.createElement('div');
    container.className = 'flash-container';
    document.body.appendChild(container);
    return container;
}

// Add to cart functionality
if (typeof addToCart === 'undefined') {
    async function addToCart(itemId, itemType, itemName) {
        try {
            const response = await fetch('/api/add_to_cart', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    id: itemId,
                    type: itemType
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update cart badge
                const cartBadge = document.querySelector('.nav-badge') || 
                                 document.querySelector('.badge');
                if (cartBadge) {
                    cartBadge.textContent = data.cart_count;
                    cartBadge.style.display = 'flex';
                }
                
                showNotification(`${itemName} added to cart`, 'success');
            } else {
                showNotification(data.message || 'Failed to add to cart', 'error');
            }
        } catch (error) {
            showNotification('Network error', 'error');
        }
    }
}

// Initialize add to cart buttons
document.addEventListener('DOMContentLoaded', function() {
    const addToCartBtns = document.querySelectorAll('.add-to-cart-btn');
    addToCartBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.getAttribute('data-id');
            const itemType = this.getAttribute('data-type');
            const itemName = this.getAttribute('data-name');
            
            addToCart(itemId, itemType, itemName);
        });
    });
});
