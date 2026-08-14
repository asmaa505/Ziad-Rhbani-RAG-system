// Initialize Markdown Parser
const md = window.markdownit({
    html: false,        // Disable HTML tags in source for security
    linkify: true,      // Autoconvert URL-like text to links
    typographer: true   // Enable smart quotes and other typographic substitutions
});

// Select DOM Elements
const chatForm = document.getElementById('chat-form');
const queryInput = document.getElementById('query-input');
const sendBtn = document.getElementById('send-btn');
const chatMessages = document.getElementById('chat-messages');
const loadingIndicator = document.getElementById('loading-indicator');
const clearBtn = document.getElementById('clear-btn');

// API Server Origin configuration
// If accessed via Live Server (port 5500) or other frontend servers, default to port 8000
const API_BASE_URL = window.location.port === '8000'
    ? window.location.origin 
    : 'http://127.0.0.1:8000';

// Cute 3D Chibi Fish Avatar HTML template
const FISH_AVATAR_HTML = `
<div class="avatar-container">
    <svg class="fish-avatar-svg" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" width="36" height="36">
        <defs>
            <radialGradient id="avatarGlow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.5"/>
                <stop offset="100%" stop-color="#E0E0E0" stop-opacity="0"/>
            </radialGradient>
            <radialGradient id="body3D" cx="35%" cy="30%" r="65%">
                <stop offset="0%" stop-color="#FFF59D"/>
                <stop offset="30%" stop-color="#FFB300"/>
                <stop offset="85%" stop-color="#FF6F00"/>
                <stop offset="100%" stop-color="#E65100"/>
            </radialGradient>
            <linearGradient id="finGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#FFE082" stop-opacity="0.9"/>
                <stop offset="100%" stop-color="#FF8C00" stop-opacity="0.6"/>
            </linearGradient>
            <filter id="cleanShadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#E65100" flood-opacity="0.3"/>
            </filter>
        </defs>
        <circle cx="60" cy="60" r="54" fill="url(#avatarGlow)" />
        <path d="M 60 20 C 50 28, 70 28, 60 20 Z" fill="url(#finGradient)" stroke="#FFB300" stroke-width="1"/>
        <path d="M 60 88 C 48 102, 72 102, 60 88 Z" fill="url(#finGradient)"/>
        <ellipse cx="26" cy="62" rx="10" ry="6" fill="url(#finGradient)" transform="rotate(-20 26 62)" filter="url(#cleanShadow)"/>
        <ellipse cx="94" cy="62" rx="10" ry="6" fill="url(#finGradient)" transform="rotate(20 94 62)" filter="url(#cleanShadow)"/>
        <circle cx="60" cy="56" r="34" fill="url(#body3D)" filter="url(#cleanShadow)"/>
        <g>
            <circle cx="44" cy="50" r="10" fill="#1A1D20"/>
            <circle cx="47" cy="46" r="4" fill="#FFFFFF"/>
            <circle cx="41" cy="54" r="1.8" fill="#FFFFFF"/>
            <circle cx="48" cy="52" r="1" fill="#FFFFFF"/>
        </g>
        <g>
            <circle cx="76" cy="50" r="10" fill="#1A1D20"/>
            <circle cx="79" cy="46" r="4" fill="#FFFFFF"/>
            <circle cx="73" cy="55" r="1.8" fill="#FFFFFF"/>
            <circle cx="80" cy="52" r="1" fill="#FFFFFF"/>
        </g>
        <ellipse cx="33" cy="60" rx="5" ry="3" fill="#FF5252" opacity="0.6"/>
        <ellipse cx="87" cy="60" rx="5" ry="3" fill="#FF5252" opacity="0.6"/>
        <path d="M 56 62 Q 60 66 64 62" fill="none" stroke="#3E2723" stroke-width="2" stroke-linecap="round"/>
        <ellipse cx="60" cy="28" rx="12" ry="5" fill="#FFFFFF" opacity="0.5"/>
    </svg>
</div>
`;

/**
 * Appends a chat bubble to the conversation window with wrapping
 * @param {string} text - Message text or HTML
 * @param {string} sender - 'user' or 'system'
 * @param {boolean} isMarkdown - Parse the text as Markdown if true
 */
function appendMessage(text, sender, isMarkdown = false) {
    // Create wrapper div for layout alignment
    const wrapperDiv = document.createElement('div');
    wrapperDiv.classList.add('message-wrapper', `${sender}-wrapper`);
    
    // Add fish avatar if sender is the assistant (system)
    if (sender === 'system') {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = FISH_AVATAR_HTML.trim();
        wrapperDiv.appendChild(tempDiv.firstChild);
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);
    
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    
    if (isMarkdown) {
        // Render Markdown content
        contentDiv.innerHTML = md.render(text);
    } else {
        // Render plain text (safe from HTML injection)
        const p = document.createElement('p');
        p.textContent = text;
        contentDiv.appendChild(p);
    }
    
    messageDiv.appendChild(contentDiv);
    wrapperDiv.appendChild(messageDiv);
    
    chatMessages.appendChild(wrapperDiv);
    
    // Smoothly scroll to the latest message
    scrollToBottom();
}

/**
 * Scroll conversation container to the bottom
 */
function scrollToBottom() {
    chatMessages.scrollTo({
        top: chatMessages.scrollHeight,
        behavior: 'smooth'
    });
}

/**
 * Displays or hides the loading spinner
 * @param {boolean} show - Show indicator if true, hide if false
 */
function setLoading(show) {
    if (show) {
        loadingIndicator.classList.remove('hidden');
        queryInput.disabled = true;
        sendBtn.disabled = true;
        scrollToBottom();
    } else {
        loadingIndicator.classList.add('hidden');
        queryInput.disabled = false;
        sendBtn.disabled = false;
    }
}

/**
 * Send request to FastAPI endpoint and display the response
 * @param {string} question - Question query string
 */
async function sendQuery(question) {
    // 1. Add user query to chat history
    appendMessage(question, 'user');
    
    // 2. Display loading state
    setLoading(true);
    
    try {
        // 3. POST request to API endpoint
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        // 4. Handle API responses
        if (response.ok && data.status === 'success') {
            appendMessage(data.answer, 'system', true);
        } else {
            const errorMsg = data.detail || 'حدث خطأ في معالجة طلبك.';
            appendMessage(`⚠️ **خطأ:** ${errorMsg}`, 'system', true);
        }
    } catch (error) {
        console.error('Fetch Error:', error);
        appendMessage('❌ **فشل الاتصال:** تعذر الوصول إلى خادم الباك-إند. يرجى التأكد من تشغيل الخادم.', 'system', true);
    } finally {
        // 5. Hide loading state
        setLoading(false);
        queryInput.focus();
    }
}

// Form Submission Event Listener
chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const question = queryInput.value.trim();
    if (!question) return;
    
    // Clear input field immediately
    queryInput.value = '';
    
    // Submit the query
    sendQuery(question);
});

// Clear Button Event Listener: Clears history except the first welcome message
clearBtn.addEventListener('click', () => {
    const welcomeMessage = chatMessages.firstElementChild;
    chatMessages.innerHTML = '';
    if (welcomeMessage && welcomeMessage.classList.contains('system-wrapper')) {
        chatMessages.appendChild(welcomeMessage);
    } else {
        // Recreate default greeting if deleted
        appendMessage(
            'أهلاً بك! كيف يمكنني مساعدتك اليوم في استكشاف أرشيف وأعمال الفنان زياد الرحباني؟',
            'system',
            false
        );
    }
    queryInput.focus();
});

/**
 * Click helper for sidebar suggestions
 * @param {string} question - Question template text
 */
function askSuggestion(question) {
    if (queryInput.disabled) return;
    sendQuery(question);
}
