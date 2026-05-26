const API_URL = "/api";

const profileInput = document.getElementById('profile-input');
const formInput = document.getElementById('form-input');
const autofillBtn = document.getElementById('autofill-btn');
const resultCard = document.getElementById('result-card');
const chatInput = document.getElementById('chat-input');
const chatSend = document.getElementById('chat-send');
const chatBody = document.getElementById('chat-body');

let profileUploaded = false;
let formUploaded = false;
let formText = "";

// Helper to update upload status
function updateStatus(elementId, status, isSuccess) {
    const el = document.getElementById(elementId);
    el.textContent = status;
    const parent = el.closest('.upload-area');
    if (isSuccess) parent.classList.add('uploaded');
    else parent.classList.remove('uploaded');
}

profileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    updateStatus('profile-status', 'Uploading...', false);
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`${API_URL}/upload-company-profile`, { method: 'POST', body: formData });
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Upload failed');
        }
        updateStatus('profile-status', file.name + ' - Uploaded', true);
        profileUploaded = true;
        enableInteractions();
    } catch (err) {
        console.error(err);
        updateStatus('profile-status', err.message || 'Upload failed', false);
        alert('Profile Upload Error: ' + err.message);
    }
});

formInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    updateStatus('form-status', 'Uploading...', false);
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`${API_URL}/upload-form`, { method: 'POST', body: formData });
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Upload failed');
        }
        const data = await res.json();
        formText = data.full_text; // Store for filling
        updateStatus('form-status', file.name + ' - Uploaded', true);
        formUploaded = true;
        enableInteractions();
    } catch (err) {
        console.error(err);
        updateStatus('form-status', err.message || 'Upload failed', false);
        alert('Form Upload Error: ' + err.message);
    }
});

function enableInteractions() {
    if (profileUploaded) {
        chatInput.disabled = false;
        chatSend.disabled = false;
    }
    if (profileUploaded && formUploaded) {
        autofillBtn.disabled = false;
    }
}

autofillBtn.addEventListener('click', async () => {
    autofillBtn.disabled = true;
    const originalText = autofillBtn.innerHTML;
    autofillBtn.innerHTML = '<i data-lucide="loader-2" class="animate-spin"></i> Processing...';
    lucide.createIcons();

    try {
        const res = await fetch(`${API_URL}/fill-form`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ form_text: formText })
        });
        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.detail || 'Failed to fill form');
        }
        resultCard.classList.remove('hidden');
    } catch (err) {
        alert('Form Filling Error: ' + err.message);
    } finally {
        autofillBtn.innerHTML = originalText;
        autofillBtn.disabled = false;
        lucide.createIcons();
    }
});

// Chat Logic
function addMessage(text, isUser) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isUser ? 'user' : 'bot'}`;
    msgDiv.innerHTML = `
        <div class="avatar"><i data-lucide="${isUser ? 'user' : 'bot'}"></i></div>
        <div class="bubble">${text}</div>
    `;
    chatBody.appendChild(msgDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
    lucide.createIcons();
}

async function handleChat() {
    const query = chatInput.value.trim();
    if (!query) return;

    addMessage(query, true);
    chatInput.value = '';
    chatInput.disabled = true;

    try {
        const res = await fetch(`${API_URL}/ask-question`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: query })
        });
        const data = await res.json();
        addMessage(data.answer, false);
    } catch (err) {
        addMessage("Error getting answer.", false);
    } finally {
        chatInput.disabled = false;
        chatInput.focus();
    }
}

chatSend.addEventListener('click', handleChat);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleChat();
});

// Check persisted session status on page load
async function initSession() {
    try {
        const res = await fetch(`${API_URL}/session-status`);
        const data = await res.json();
        
        if (data.profile_uploaded) {
            profileUploaded = true;
            updateStatus('profile-status', 'Persisted Knowledge Base - Loaded', true);
        }
        if (data.form_uploaded) {
            formUploaded = true;
            formText = data.form_text || "";
            updateStatus('form-status', data.form_filename + ' - Loaded', true);
        }
        if (data.has_filled_response) {
            resultCard.classList.remove('hidden');
        }
        enableInteractions();
    } catch (err) {
        console.error("Failed to restore session:", err);
    }
}

// Call on page load
initSession();
