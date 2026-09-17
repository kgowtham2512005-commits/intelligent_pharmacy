/* ═══════════════════════════════════════════════════════════════════════
   RuralCare AI — Conversational Voice Assistant (Phase 13 + 14)
   Full-featured voice assistant with STT, TTS, NLP, and multi-language.
   ═══════════════════════════════════════════════════════════════════════ */

(() => {
  'use strict';

  // ── State ──────────────────────────────────────────────────────────
  let currentLang = 'en';
  let isListening = false;
  let isSpeaking = false;
  let recognition = null;
  let conversationHistory = [];

  const LANG_CONFIG = {
    en: { code: 'en-US', label: 'English', flag: '🇬🇧', voiceLang: 'en' },
    ta: { code: 'ta-IN', label: 'தமிழ்', flag: '🇮🇳', voiceLang: 'ta' },
    hi: { code: 'hi-IN', label: 'हिंदी', flag: '🇮🇳', voiceLang: 'hi' }
  };

  // ── Initialize on DOM Ready ────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    injectAssistantUI();
    setupSpeechRecognition();
    bindEvents();
  });

  // ── Inject Assistant Floating Button + Panel into Page ─────────────
  function injectAssistantUI() {
    const assistantHTML = `
      <!-- Floating Voice Assistant Button -->
      <button id="voiceAssistantFab" class="voice-fab" title="RuralCare AI Voice Assistant" aria-label="Open Voice Assistant">
        <i class="bi bi-mic-fill voice-fab-icon"></i>
        <span class="voice-fab-pulse"></span>
      </button>

      <!-- Voice Assistant Panel -->
      <div id="voiceAssistantPanel" class="voice-panel voice-panel-hidden">
        <!-- Panel Header -->
        <div class="voice-panel-header">
          <div class="d-flex align-items-center gap-2">
            <div class="voice-panel-logo">
              <i class="bi bi-robot"></i>
            </div>
            <div>
              <h6 class="mb-0 fw-bold text-white">RuralCare AI Assistant</h6>
              <small class="voice-status-text" id="voiceStatusText">Tap mic to speak</small>
            </div>
          </div>
          <div class="d-flex align-items-center gap-2">
            <!-- Language Selector -->
            <div class="dropdown">
              <button class="btn btn-sm btn-outline-light rounded-pill px-2 py-1 dropdown-toggle" type="button" id="langDropdown" data-bs-toggle="dropdown" aria-expanded="false" style="font-size: 0.75rem;">
                <span id="currentLangFlag">🇬🇧</span> <span id="currentLangLabel">EN</span>
              </button>
              <ul class="dropdown-menu dropdown-menu-end dropdown-menu-dark" aria-labelledby="langDropdown">
                <li><a class="dropdown-item lang-option active" href="#" data-lang="en">🇬🇧 English</a></li>
                <li><a class="dropdown-item lang-option" href="#" data-lang="ta">🇮🇳 தமிழ் (Tamil)</a></li>
                <li><a class="dropdown-item lang-option" href="#" data-lang="hi">🇮🇳 हिंदी (Hindi)</a></li>
              </ul>
            </div>
            <button class="btn btn-sm btn-outline-light rounded-circle p-0" id="closeAssistantBtn" style="width:28px;height:28px;line-height:28px;" title="Close">
              <i class="bi bi-x-lg" style="font-size:0.7rem;"></i>
            </button>
          </div>
        </div>

        <!-- Chat Area -->
        <div class="voice-chat-area" id="voiceChatArea">
          <!-- Welcome message injected dynamically -->
        </div>

        <!-- Quick Symptom Chips -->
        <div class="voice-chips-area" id="voiceChipsArea">
          <div class="voice-chips-scroll">
            <button class="voice-chip" data-query="I have a headache"><i class="bi bi-emoji-dizzy me-1"></i>Headache</button>
            <button class="voice-chip" data-query="I have fever"><i class="bi bi-thermometer-half me-1"></i>Fever</button>
            <button class="voice-chip" data-query="I have cold"><i class="bi bi-snow me-1"></i>Cold</button>
            <button class="voice-chip" data-query="I have acidity"><i class="bi bi-droplet me-1"></i>Acidity</button>
            <button class="voice-chip" data-query="I have allergy"><i class="bi bi-flower1 me-1"></i>Allergy</button>
            <button class="voice-chip" data-query="I have stomach pain"><i class="bi bi-bandaid me-1"></i>Stomach</button>
            <button class="voice-chip" data-query="I have cough"><i class="bi bi-wind me-1"></i>Cough</button>
            <button class="voice-chip" data-query="I need ORS"><i class="bi bi-cup-straw me-1"></i>ORS</button>
          </div>
        </div>

        <!-- Input Area -->
        <div class="voice-input-area">
          <div class="voice-input-row">
            <input type="text" id="voiceTextInput" class="voice-text-input" placeholder="Type or tap mic to ask..." autocomplete="off">
            <button id="voiceSendBtn" class="voice-send-btn" title="Send">
              <i class="bi bi-send-fill"></i>
            </button>
            <button id="voiceMicBtn" class="voice-mic-btn" title="Start Listening">
              <i class="bi bi-mic-fill" id="voiceMicIcon"></i>
            </button>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', assistantHTML);

    // Show welcome message
    setTimeout(() => {
      addAssistantMessage(getWelcomeMessage(), false);
    }, 300);
  }

  // ── Setup Web Speech Recognition ──────────────────────────────────
  function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.log('Speech Recognition not supported in this browser');
      return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.lang = LANG_CONFIG[currentLang].code;

    recognition.onstart = () => {
      isListening = true;
      updateMicUI(true);
      setStatus('Listening... Speak now');
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.trim();
      if (transcript) {
        addUserMessage(transcript);
        processQuery(transcript);
      }
    };

    recognition.onerror = (event) => {
      isListening = false;
      updateMicUI(false);
      if (event.error === 'not-allowed' || event.error === 'permission-denied') {
        setStatus('Mic permission denied');
        addAssistantMessage('⚠️ Microphone access was denied. Please allow microphone permission in your browser settings, or type your question below.', false);
      } else if (event.error === 'no-speech') {
        setStatus('No speech detected');
        addAssistantMessage('I didn\'t hear anything. Please try again or type your question.', false);
      } else {
        setStatus('Tap mic to speak');
      }
    };

    recognition.onend = () => {
      isListening = false;
      updateMicUI(false);
      if (!isSpeaking) {
        setStatus('Tap mic to speak');
      }
    };
  }

  // ── Bind Events ───────────────────────────────────────────────────
  function bindEvents() {
    // FAB button
    const fab = document.getElementById('voiceAssistantFab');
    const panel = document.getElementById('voiceAssistantPanel');
    const closeBtn = document.getElementById('closeAssistantBtn');
    const micBtn = document.getElementById('voiceMicBtn');
    const sendBtn = document.getElementById('voiceSendBtn');
    const textInput = document.getElementById('voiceTextInput');

    fab.addEventListener('click', () => {
      panel.classList.toggle('voice-panel-hidden');
      fab.classList.toggle('voice-fab-active');
      if (!panel.classList.contains('voice-panel-hidden')) {
        textInput.focus();
      }
    });

    closeBtn.addEventListener('click', () => {
      panel.classList.add('voice-panel-hidden');
      fab.classList.remove('voice-fab-active');
      stopSpeaking();
    });

    // Mic button
    micBtn.addEventListener('click', () => {
      if (isListening) {
        stopListening();
      } else {
        startListening();
      }
    });

    // Send button
    sendBtn.addEventListener('click', () => {
      sendTextInput();
    });

    // Enter key
    textInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        sendTextInput();
      }
    });

    // Quick chip buttons
    document.querySelectorAll('.voice-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const query = chip.dataset.query;
        addUserMessage(query);
        processQuery(query);
      });
    });

    // Language selector
    document.querySelectorAll('.lang-option').forEach(opt => {
      opt.addEventListener('click', (e) => {
        e.preventDefault();
        const lang = opt.dataset.lang;
        switchLanguage(lang);

        // Update active state
        document.querySelectorAll('.lang-option').forEach(o => o.classList.remove('active'));
        opt.classList.add('active');
      });
    });
  }

  // ── Speech Recognition Controls ───────────────────────────────────
  function startListening() {
    if (!recognition) {
      addAssistantMessage('⚠️ Voice recognition is not supported in this browser. Please type your question instead.', false);
      return;
    }
    stopSpeaking();
    try {
      recognition.lang = LANG_CONFIG[currentLang].code;
      recognition.start();
    } catch (e) {
      // Already started
      console.log('Recognition already started');
    }
  }

  function stopListening() {
    if (recognition && isListening) {
      recognition.stop();
    }
  }

  // ── Text-to-Speech (TTS) ──────────────────────────────────────────
  function speakText(text) {
    if (!('speechSynthesis' in window)) return;

    stopSpeaking();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = LANG_CONFIG[currentLang].code;
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Try to find a voice matching the language
    const voices = speechSynthesis.getVoices();
    const langPrefix = LANG_CONFIG[currentLang].code.split('-')[0];
    const matchingVoice = voices.find(v => v.lang.startsWith(langPrefix));
    if (matchingVoice) {
      utterance.voice = matchingVoice;
    }

    utterance.onstart = () => {
      isSpeaking = true;
      setStatus('Speaking...');
    };
    utterance.onend = () => {
      isSpeaking = false;
      setStatus('Tap mic to speak');
    };
    utterance.onerror = () => {
      isSpeaking = false;
      setStatus('Tap mic to speak');
    };

    speechSynthesis.speak(utterance);
  }

  function stopSpeaking() {
    if ('speechSynthesis' in window) {
      speechSynthesis.cancel();
    }
    isSpeaking = false;
  }

  // ── Process Query via Backend API ─────────────────────────────────
  async function processQuery(queryText) {
    setStatus('Thinking...');
    showTypingIndicator();

    try {
      const response = await fetch('/api/voice/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText, lang: currentLang })
      });

      const data = await response.json();
      removeTypingIndicator();

      if (data.status === 'success' || data.status === 'error') {
        // Build rich response HTML
        let messageHTML = `<p>${data.spoken_response || 'Sorry, something went wrong.'}</p>`;

        // Add medicine result cards if available
        if (data.results && data.results.length > 0) {
          messageHTML += buildResultCards(data.results);
        }

        // Add suggestion chips
        if (data.suggestions && data.suggestions.length > 0) {
          messageHTML += buildSuggestionChips(data.suggestions);
        }

        addAssistantMessage(messageHTML, true);

        // Speak the response
        if (data.spoken_response) {
          speakText(data.spoken_response);
        }
      }
    } catch (error) {
      removeTypingIndicator();
      addAssistantMessage('⚠️ Could not connect to the server. Please check your connection and try again.', false);
      setStatus('Connection error');
      console.error('Voice assistant error:', error);
    }
  }

  // ── Build Rich Result Cards HTML ──────────────────────────────────
  function buildResultCards(results) {
    let html = '<div class="voice-results">';
    results.slice(0, 4).forEach(med => {
      const priceText = med.lowest_price ? `₹${med.lowest_price.toFixed(2)}` : 'N/A';
      const availBadge = med.available_count > 0
        ? `<span class="badge bg-success-subtle text-success" style="font-size:0.65rem;">✓ ${med.available_count} shop(s)</span>`
        : `<span class="badge bg-danger-subtle text-danger" style="font-size:0.65rem;">✗ Out of stock</span>`;

      html += `
        <a href="/medicine/${med.medicine_id}" class="voice-result-card text-decoration-none">
          <div class="d-flex justify-content-between align-items-start">
            <div>
              <div class="voice-result-name">${med.name}</div>
              ${med.generic_name ? `<div class="voice-result-generic">${med.generic_name}</div>` : ''}
            </div>
            <div class="text-end">
              <div class="voice-result-price">${priceText}</div>
              ${availBadge}
            </div>
          </div>
          ${med.cheapest_pharmacy ? `<div class="voice-result-pharmacy"><i class="bi bi-shop me-1"></i>${med.cheapest_pharmacy}</div>` : ''}
        </a>
      `;
    });
    html += '</div>';
    return html;
  }

  // ── Build Suggestion Chips ────────────────────────────────────────
  function buildSuggestionChips(suggestions) {
    let html = '<div class="voice-suggestions">';
    suggestions.forEach(s => {
      html += `<button class="voice-suggestion-chip" onclick="document.dispatchEvent(new CustomEvent('voiceSuggestion', {detail:'${s.replace(/'/g, "\\'")}'}))">${s}</button>`;
    });
    html += '</div>';
    return html;
  }

  // Listen for suggestion chip clicks
  document.addEventListener('voiceSuggestion', (e) => {
    const query = e.detail;
    addUserMessage(query);
    processQuery(query);
  });

  // ── Chat Message Helpers ──────────────────────────────────────────
  function addUserMessage(text) {
    const chatArea = document.getElementById('voiceChatArea');
    const msg = document.createElement('div');
    msg.className = 'voice-msg voice-msg-user';
    msg.innerHTML = `<div class="voice-msg-bubble voice-msg-bubble-user">${escapeHTML(text)}</div>`;
    chatArea.appendChild(msg);
    scrollToBottom();
    conversationHistory.push({ role: 'user', text });
  }

  function addAssistantMessage(html, isRich = false) {
    const chatArea = document.getElementById('voiceChatArea');
    const msg = document.createElement('div');
    msg.className = 'voice-msg voice-msg-assistant';
    msg.innerHTML = `
      <div class="voice-msg-avatar"><i class="bi bi-robot"></i></div>
      <div class="voice-msg-bubble voice-msg-bubble-assistant">${isRich ? html : escapeHTML(html)}</div>
    `;
    chatArea.appendChild(msg);
    scrollToBottom();

    // Re-bind suggestion chips within this message
    msg.querySelectorAll('.voice-suggestion-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const query = chip.textContent;
        addUserMessage(query);
        processQuery(query);
      });
    });

    conversationHistory.push({ role: 'assistant', text: html });
  }

  function showTypingIndicator() {
    const chatArea = document.getElementById('voiceChatArea');
    const indicator = document.createElement('div');
    indicator.id = 'typingIndicator';
    indicator.className = 'voice-msg voice-msg-assistant';
    indicator.innerHTML = `
      <div class="voice-msg-avatar"><i class="bi bi-robot"></i></div>
      <div class="voice-msg-bubble voice-msg-bubble-assistant">
        <div class="voice-typing">
          <span></span><span></span><span></span>
        </div>
      </div>
    `;
    chatArea.appendChild(indicator);
    scrollToBottom();
  }

  function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();
  }

  function scrollToBottom() {
    const chatArea = document.getElementById('voiceChatArea');
    setTimeout(() => {
      chatArea.scrollTop = chatArea.scrollHeight;
    }, 50);
  }

  // ── UI Updates ────────────────────────────────────────────────────
  function updateMicUI(listening) {
    const micBtn = document.getElementById('voiceMicBtn');
    const micIcon = document.getElementById('voiceMicIcon');
    if (listening) {
      micBtn.classList.add('voice-mic-active');
      micIcon.className = 'bi bi-mic-fill';
    } else {
      micBtn.classList.remove('voice-mic-active');
      micIcon.className = 'bi bi-mic-fill';
    }
  }

  function setStatus(text) {
    const el = document.getElementById('voiceStatusText');
    if (el) el.textContent = text;
  }

  function sendTextInput() {
    const input = document.getElementById('voiceTextInput');
    const text = input.value.trim();
    if (text) {
      addUserMessage(text);
      processQuery(text);
      input.value = '';
    }
  }

  // ── Language Switching ────────────────────────────────────────────
  function switchLanguage(lang) {
    currentLang = lang;
    const config = LANG_CONFIG[lang];

    document.getElementById('currentLangFlag').textContent = config.flag;
    document.getElementById('currentLangLabel').textContent = config.label.substring(0, 2).toUpperCase();

    if (recognition) {
      recognition.lang = config.code;
    }

    // Update placeholder
    const placeholders = {
      en: 'Type or tap mic to ask...',
      ta: 'தட்டச்சு செய்யவும் அல்லது மைக் தட்டவும்...',
      hi: 'टाइप करें या माइक टैप करें...'
    };
    document.getElementById('voiceTextInput').placeholder = placeholders[lang] || placeholders.en;

    addAssistantMessage(`🌐 Language switched to ${config.flag} ${config.label}`, false);
  }

  // ── Welcome Message ───────────────────────────────────────────────
  function getWelcomeMessage() {
    const msgs = {
      en: '👋 Hello! I\'m your RuralCare AI Voice Assistant. Ask me about medicines, symptoms, or nearby pharmacies. Try saying "I have a headache" or tap a chip below!',
      ta: '👋 வணக்கம்! நான் உங்கள் RuralCare AI குரல் உதவியாளர். மருந்துகள், அறிகுறிகள் பற்றி கேளுங்கள்.',
      hi: '👋 नमस्ते! मैं आपका RuralCare AI वॉयस असिस्टेंट हूँ। दवाइयों, लक्षणों के बारे में पूछें।'
    };
    return msgs[currentLang] || msgs.en;
  }

  // ── Utility ───────────────────────────────────────────────────────
  function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

})();
