/* RuralCare AI Customer Search & Geolocation Logic */

let userLat = null;
let userLng = null;

document.addEventListener('DOMContentLoaded', () => {
  initGeolocation();
  initVoiceSearch();
  initSearchAutocomplete();
});

// Geolocation Handling (Phase 11)
function initGeolocation() {
  const locBadge = document.getElementById('locationStatusBadge');
  
  if ("geolocation" in navigator) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        userLat = position.coords.latitude;
        userLng = position.coords.longitude;

        if (locBadge) {
          locBadge.className = "badge bg-success bg-opacity-10 text-success border border-success px-3 py-2 rounded-pill";
          locBadge.innerHTML = `<i class="bi bi-geo-alt-fill me-1"></i> Location Enabled (${userLat.toFixed(2)}, ${userLng.toFixed(2)})`;
        }

        updateLocationInLinks();
      },
      (error) => {
        console.log("Geolocation permission denied or unavailable:", error.message);
        if (locBadge) {
          locBadge.className = "badge bg-secondary bg-opacity-10 text-secondary border border-secondary px-3 py-2 rounded-pill";
          locBadge.innerHTML = `<i class="bi bi-geo-alt me-1"></i> Location Optional (Prices & Stock Available)`;
        }
      },
      { timeout: 5000 }
    );
  }
}

function updateLocationInLinks() {
  if (!userLat || !userLng) return;

  // Add hidden lat/lng inputs to search forms
  document.querySelectorAll('form.search-form').forEach(form => {
    let latInput = form.querySelector('input[name="lat"]');
    if (!latInput) {
      latInput = document.createElement('input');
      latInput.type = 'hidden';
      latInput.name = 'lat';
      form.appendChild(latInput);
    }
    latInput.value = userLat;

    let lngInput = form.querySelector('input[name="lng"]');
    if (!lngInput) {
      lngInput = document.createElement('input');
      lngInput.type = 'hidden';
      lngInput.name = 'lng';
      form.appendChild(lngInput);
    }
    lngInput.value = userLng;
  });

  // Append lat & lng query params to medicine detail links
  document.querySelectorAll('a.medicine-link').forEach(link => {
    const url = new URL(link.href, window.location.origin);
    url.searchParams.set('lat', userLat);
    url.searchParams.set('lng', userLng);
    link.href = url.toString();
  });
}

// Web Speech API Voice Search with Failover (Phase 14)
function initVoiceSearch() {
  const voiceBtn = document.getElementById('voiceSearchBtn');
  const searchInput = document.getElementById('searchInput');
  const voiceAlertContainer = document.getElementById('voiceAlertContainer');

  if (!voiceBtn || !searchInput) return;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    voiceBtn.addEventListener('click', () => {
      showVoiceAlert("Voice search is not supported in this browser. Please type the medicine name.");
    });
    voiceBtn.setAttribute('title', 'Voice search is not supported in this browser. Please type the medicine name.');
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  voiceBtn.addEventListener('click', () => {
    try {
      recognition.start();
      voiceBtn.classList.add('btn-danger', 'animate-pulse');
      voiceBtn.classList.remove('btn-outline-secondary');
      voiceBtn.innerHTML = '<i class="bi bi-mic-fill me-1"></i> Listening...';
    } catch (e) {
      showVoiceAlert("Voice search is already listening or initializing. Please speak now.");
    }
  });

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript.trim();
    if (transcript) {
      searchInput.value = transcript;
      resetVoiceBtn(voiceBtn);

      // Auto-submit search form
      const form = searchInput.closest('form');
      if (form) form.submit();
    } else {
      showVoiceAlert("No speech detected. Please try speaking again or type your medicine name.");
      resetVoiceBtn(voiceBtn);
    }
  };

  recognition.onerror = (event) => {
    resetVoiceBtn(voiceBtn);
    if (event.error === 'not-allowed' || event.error === 'permission-denied') {
      showVoiceAlert("Microphone access denied. Please allow microphone permissions or type your search query.");
    } else if (event.error === 'no-speech') {
      showVoiceAlert("No speech detected. Please try speaking again or type your medicine name.");
    } else {
      showVoiceAlert(`Voice recognition error (${event.error}). Please type your medicine name.`);
    }
  };

  recognition.onend = () => {
    resetVoiceBtn(voiceBtn);
  };
}

function resetVoiceBtn(voiceBtn) {
  voiceBtn.classList.remove('btn-danger', 'animate-pulse');
  voiceBtn.classList.add('btn-outline-secondary');
  voiceBtn.innerHTML = '<i class="bi bi-mic"></i>';
}

function showVoiceAlert(message) {
  let alertBox = document.getElementById('voiceAlertBox');
  if (!alertBox) {
    const container = document.getElementById('voiceAlertContainer') || document.querySelector('.search-form')?.parentElement;
    if (container) {
      alertBox = document.createElement('div');
      alertBox.id = 'voiceAlertBox';
      alertBox.className = 'alert alert-warning alert-dismissible fade show mt-2 shadow-sm small text-start';
      container.appendChild(alertBox);
    }
  }

  if (alertBox) {
    alertBox.innerHTML = `
      <i class="bi bi-exclamation-triangle-fill me-2"></i> ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    setTimeout(() => {
      if (alertBox && alertBox.parentElement) {
        alertBox.remove();
      }
    }, 6000);
  } else {
    alert(message);
  }
}

// Autocomplete Live Search (Phase 10)
function initSearchAutocomplete() {
  const searchInput = document.getElementById('searchInput');
  const autocompleteContainer = document.getElementById('autocompleteDropdown');

  if (!searchInput || !autocompleteContainer) return;

  let debounceTimer;

  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const query = searchInput.value.trim();

    if (query.length < 2) {
      autocompleteContainer.classList.add('d-none');
      autocompleteContainer.innerHTML = '';
      return;
    }

    debounceTimer = setTimeout(() => {
      fetch(`/api/medicines/search?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success' && data.results.length > 0) {
            let html = '<ul class="list-group shadow-lg border-0 rounded-3">';
            data.results.slice(0, 5).forEach(med => {
              const priceText = med.lowest_price ? `From ₹${med.lowest_price.toFixed(2)}` : 'Out of stock';
              const badgeClass = med.available_pharmacies_count > 0 ? 'bg-success-subtle text-success' : 'bg-secondary-subtle text-secondary';
              
              html += `
                <li class="list-group-item list-group-item-action p-3">
                  <a href="/medicine/${med.medicine_id}" class="text-decoration-none text-dark d-flex justify-content-between align-items-center medicine-link">
                    <div>
                      <strong class="fs-6">${med.medicine_name}</strong>
                      ${med.generic_name ? `<div class="small text-muted">${med.generic_name}</div>` : ''}
                    </div>
                    <div class="text-end">
                      <span class="badge ${badgeClass} px-2 py-1">${priceText}</span>
                      <div class="small text-muted mt-1">${med.available_pharmacies_count} shop(s)</div>
                    </div>
                  </a>
                </li>
              `;
            });
            html += '</ul>';
            autocompleteContainer.innerHTML = html;
            autocompleteContainer.classList.remove('d-none');
            updateLocationInLinks();
          } else {
            autocompleteContainer.innerHTML = `
              <div class="list-group shadow-lg border-0 rounded-3 p-3 text-muted text-center">
                <i class="bi bi-exclamation-circle me-1"></i> Medicine not found.
              </div>
            `;
            autocompleteContainer.classList.remove('d-none');
          }
        })
        .catch(err => console.error("Autocomplete error:", err));
    }, 300);
  });

  // Hide autocomplete on click outside
  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !autocompleteContainer.contains(e.target)) {
      autocompleteContainer.classList.add('d-none');
    }
  });
}
