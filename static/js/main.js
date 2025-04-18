document.addEventListener('DOMContentLoaded', function() {
    // Show/hide navigation menu on mobile
    const menuToggle = document.getElementById('menu-toggle');
    const navMenu = document.getElementById('nav-menu');
    
    if (menuToggle && navMenu) {
      menuToggle.addEventListener('click', function() {
        navMenu.classList.toggle('show');
      });
    }
  
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
      form.addEventListener('submit', event => {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        
        form.classList.add('was-validated');
      }, false);
    });
  
    // Show image preview on upload
    const imageInput = document.getElementById('image-upload');
    const imagePreview = document.getElementById('image-preview');
    
    if (imageInput && imagePreview) {
      imageInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
          const reader = new FileReader();
          reader.addEventListener('load', function() {
            imagePreview.src = this.result;
            imagePreview.style.display = 'block';
          });
          reader.readAsDataURL(file);
        }
      });
    }
  
    // Filter items by category
    const categoryFilters = document.querySelectorAll('.category-filter');
    const itemCards = document.querySelectorAll('.item-card');
    
    if (categoryFilters.length && itemCards.length) {
      categoryFilters.forEach(filter => {
        filter.addEventListener('click', function(e) {
          e.preventDefault();
          
          // Remove active class from all filters
          categoryFilters.forEach(f => f.classList.remove('active'));
          
          // Add active class to clicked filter
          this.classList.add('active');
          
          const category = this.dataset.category;
          
          if (category === 'all') {
            // Show all items
            itemCards.forEach(item => {
              item.style.display = 'flex';
            });
          } else {
            // Filter items by category
            itemCards.forEach(item => {
              if (item.dataset.category === category) {
                item.style.display = 'flex';
              } else {
                item.style.display = 'none';
              }
            });
          }
        });
      });
    }
  
    // Notifications
    const notificationBell = document.getElementById('notification-bell');
    const notificationDropdown = document.getElementById('notification-dropdown');
    
    if (notificationBell && notificationDropdown) {
      notificationBell.addEventListener('click', function(e) {
        e.preventDefault();
        notificationDropdown.classList.toggle('show');
      });
      
      // Close dropdown when clicking outside
      document.addEventListener('click', function(e) {
        if (!notificationBell.contains(e.target) && !notificationDropdown.contains(e.target)) {
          notificationDropdown.classList.remove('show');
        }
      });
    }
  
    // Mark notification as read
    const notificationItems = document.querySelectorAll('.notification-item');
    
    if (notificationItems.length) {
      notificationItems.forEach(item => {
        item.addEventListener('click', function() {
          const notificationId = this.dataset.id;
          
          // Send request to mark notification as read
          fetch(`/api/notifications/${notificationId}/mark_read/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCookie('csrftoken')
            },
          })
            .then(response => response.json())
            .then(data => {
              // Update UI to reflect read status
              this.classList.remove('unread');
              this.classList.add('read');
              
              // Update notification counter
              const counter = document.getElementById('notification-counter');
              if (counter) {
                const count = parseInt(counter.textContent) - 1;
                counter.textContent = count > 0 ? count : '';
                if (count <= 0) {
                  counter.style.display = 'none';
                }
              }
            })
            .catch(error => console.error('Error marking notification as read:', error));
        });
      });
    }
  
    // Get CSRF token from cookies
    function getCookie(name) {
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
  
    // Map initialization (if map element exists)
    const mapElement = document.getElementById('map');
    if (mapElement && window.L) {  // Check if Leaflet is loaded
      const map = L.map('map').setView([0, 0], 2);
      
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);
      
      // Add item markers to map
      const itemLocations = document.querySelectorAll('[data-latitude][data-longitude]');
      
      if (itemLocations.length) {
        const bounds = L.latLngBounds();
        
        itemLocations.forEach(item => {
          const lat = parseFloat(item.dataset.latitude);
          const lng = parseFloat(item.dataset.longitude);
          const title = item.dataset.title;
          const status = item.dataset.status;
          const url = item.dataset.url;
          
          if (lat && lng) {
            const marker = L.marker([lat, lng]).addTo(map);
            
            marker.bindPopup(`
              <strong>${title}</strong><br>
              Status: ${status}<br>
              <a href="${url}">View details</a>
            `);
            
            bounds.extend([lat, lng]);
          }
        });
        
        if (bounds.isValid()) {
          map.fitBounds(bounds);
        }
      }
    }
  });