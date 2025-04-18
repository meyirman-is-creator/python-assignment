document.addEventListener('DOMContentLoaded', function() {
  // Mobile menu toggle
  const menuToggle = document.getElementById('menu-toggle');
  const navMenu = document.getElementById('nav-menu');

  if (menuToggle && navMenu) {
    menuToggle.addEventListener('click', function() {
      navMenu.classList.toggle('active');
      menuToggle.classList.toggle('active');
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

  // Handle notification dropdown
  const notificationBell = document.getElementById('notification-bell');
  const notificationDropdown = document.getElementById('notification-dropdown');

  if (notificationBell && notificationDropdown) {
    notificationBell.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      notificationDropdown.style.display = notificationDropdown.style.display === 'block' ? 'none' : 'block';

      // Close user dropdown if open
      const userDropdown = document.querySelector('.user-dropdown');
      if (userDropdown) {
        userDropdown.style.display = 'none';
      }
    });
  }

  // Handle user dropdown
  const userLink = document.querySelector('.user-link');
  const userDropdown = document.querySelector('.user-dropdown');

  if (userLink && userDropdown) {
    userLink.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      userDropdown.style.display = userDropdown.style.display === 'block' ? 'none' : 'block';

      // Close notification dropdown if open
      if (notificationDropdown) {
        notificationDropdown.style.display = 'none';
      }
    });
  }

  // Close dropdowns when clicking outside
  document.addEventListener('click', function(e) {
    if (notificationDropdown && notificationBell &&
        !notificationBell.contains(e.target) &&
        !notificationDropdown.contains(e.target)) {
      notificationDropdown.style.display = 'none';
    }

    if (userDropdown && userLink &&
        !userLink.contains(e.target) &&
        !userDropdown.contains(e.target)) {
      userDropdown.style.display = 'none';
    }
  });

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

            // Navigate to related item if available
            if (this.dataset.url) {
              window.location.href = this.dataset.url;
            }
          })
          .catch(error => {
            console.error('Error marking notification as read:', error);
            // Fallback to direct navigation if AJAX fails
            window.location.href = `/notifications/mark-read/${notificationId}/`;
          });
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

  // Dismissible alerts
  const closeButtons = document.querySelectorAll('[data-dismiss="alert"]');
  closeButtons.forEach(button => {
    button.addEventListener('click', function() {
      const alert = this.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-20px)';
        alert.style.transition = 'opacity 0.3s, transform 0.3s';
        setTimeout(() => {
          alert.remove();
        }, 300);
      }
    });
  });

  // Auto-dismiss alerts after 5 seconds
  setTimeout(() => {
    document.querySelectorAll('.alert').forEach(alert => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-20px)';
      alert.style.transition = 'opacity 0.3s, transform 0.3s';
      setTimeout(() => {
        if (alert.parentNode) {
          alert.remove();
        }
      }, 300);
    });
  }, 5000);

  // Map initialization (if map element exists)
  const mapElement = document.getElementById('map');
  if (mapElement && window.L) {  // Check if Leaflet is loaded
    const lat = parseFloat(mapElement.dataset.latitude || 0);
    const lng = parseFloat(mapElement.dataset.longitude || 0);
    const title = mapElement.dataset.title;
    const status = mapElement.dataset.status;
    const url = mapElement.dataset.url;

    const map = L.map('map').setView([lat, lng], 15);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    if (lat && lng) {
      const marker = L.marker([lat, lng]).addTo(map);

      if (title) {
        marker.bindPopup(`
          <strong>${title}</strong><br>
          ${status ? `Статус: ${status}` : ''}
        `).openPopup();
      }
    }
  }
});