// Global State
let userId = null;
let conversationId = null;

// Tab Switching
function switchTab(tabId) {
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    document.getElementById('nav-' + tabId).classList.add('active');

    // Update content
    document.getElementById('tab-chat').classList.add('hidden');
    document.getElementById('tab-memory').classList.add('hidden');
    document.getElementById('tab-' + tabId).classList.remove('hidden');

    if (tabId === 'memory') {
        loadMemoryDashboard();
    }
}

// Format markdown-like bold to HTML
function formatMessage(text) {
    // Very basic formatting for bold and paragraphs
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
               .replace(/\n/g, '<br/>');
}

// Add message to chat
function appendMessage(role, content) {
    const chatMessages = document.getElementById('chat-messages');
    
    const wrapper = document.createElement('div');
    wrapper.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;
    
    const maxW = role === 'user' ? 'max-w-[75%]' : 'max-w-[85%] md:max-w-[70%]';
    
    let innerHTML = '';
    
    if (role === 'user') {
        innerHTML = `
            <div class="${maxW}">
                <div class="flex items-center justify-end gap-2 mb-1">
                    <span class="text-xs font-medium text-brand-textMuted">You</span>
                    <div class="w-6 h-6 rounded-full bg-brand-orange flex items-center justify-center text-white text-[10px] font-bold">TU</div>
                </div>
                <div class="bento-card p-4 rounded-tr-sm bg-brand-orange text-white text-[16px] leading-[26px] border-none shadow-soft">
                    ${formatMessage(content)}
                </div>
            </div>
        `;
    } else {
        innerHTML = `
            <div class="${maxW}">
                <div class="flex items-center gap-2 mb-1">
                    <div class="w-6 h-6 rounded-md bg-brand-blue flex items-center justify-center text-white text-[10px] font-bold shadow-soft">VS</div>
                    <span class="text-xs font-medium text-brand-textMuted">Dr. Sarabhai</span>
                </div>
                <div class="bento-card p-4 rounded-tl-sm text-brand-charcoal text-[16px] leading-[26px] shadow-sm">
                    ${formatMessage(content)}
                </div>
            </div>
        `;
    }
    
    wrapper.innerHTML = innerHTML;
    chatMessages.appendChild(wrapper);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function setLoading(isLoading) {
    const btnText = document.getElementById('btn-text');
    const btnIcon = document.getElementById('btn-icon');
    const btnLoader = document.getElementById('btn-loader');
    const input = document.getElementById('chat-input');
    
    if (isLoading) {
        btnText.classList.add('hidden');
        btnIcon.classList.add('hidden');
        btnLoader.classList.remove('hidden');
        input.disabled = true;
    } else {
        btnText.classList.remove('hidden');
        btnIcon.classList.remove('hidden');
        btnLoader.classList.add('hidden');
        input.disabled = false;
        input.focus();
    }
}

// Chat Submission
document.getElementById('chat-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!userId || !conversationId) {
        alert("Session not ready yet. Please wait...");
        return;
    }
    
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    const mode = document.getElementById('chat-mode').value;
    
    if (!message) return;
    
    input.value = '';
    appendMessage('user', message);
    setLoading(true);
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                conversation_id: conversationId,
                message: message,
                mode: mode
            })
        });
        
        if (!response.ok) throw new Error("API Error");
        
        const data = await response.json();
        appendMessage('bot', data.response);
        
    } catch (err) {
        console.error(err);
        appendMessage('bot', 'Sorry, I encountered an error while processing your request.');
    } finally {
        setLoading(false);
    }
});

// Memory Dashboard
async function loadMemoryDashboard() {
    if (!userId) return;
    
    try {
        const response = await fetch(`/memory/${userId}/dashboard`);
        if (!response.ok) return;
        
        const data = await response.json();
        
        const renderList = (elementId, items) => {
            const el = document.getElementById(elementId);
            if (!items || items.length === 0) {
                el.innerHTML = '<li class="text-sm text-brand-textMuted italic">No data yet.</li>';
                return;
            }
            el.innerHTML = items.map(i => `<li class="text-[15px] font-medium leading-tight py-2 border-b border-brand-border last:border-0">${i}</li>`).join('');
        };
        
        renderList('memory-interests', data.interests);
        renderList('memory-projects', data.projects);
        
        const bgEl = document.getElementById('memory-background');
        if (data.background && data.background.length > 0) {
            bgEl.innerHTML = data.background.map(b => `<p class="mb-3 last:mb-0">${b}</p>`).join('');
        } else {
            bgEl.innerHTML = '<span class="text-brand-textMuted italic">No background information gathered yet.</span>';
        }
        
    } catch (err) {
        console.error("Failed to load memory", err);
    }
}

// Initialization
async function initApp() {
    try {
        // Login
        const loginRes = await fetch('/users/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: 'test_user', display_name: 'Test User' })
        });
        const userData = await loginRes.json();
        userId = userData.id;
        
        // Start Conversation
        const convRes = await fetch('/conversations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        const convData = await convRes.json();
        conversationId = convData.id;
        
        console.log("Session established:", { userId, conversationId });
        
    } catch (err) {
        console.error("Failed to initialize app", err);
    }
}

// Run on load
window.addEventListener('DOMContentLoaded', initApp);
