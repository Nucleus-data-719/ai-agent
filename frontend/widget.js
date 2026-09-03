// Configuration
const API_URL = '';
// For local testing, uncomment this:
// const API_URL = 'http://localhost:8000';

let conversationId = null;

// DOM Elements
const chatToggle = document.getElementById('chat-toggle');
const chatWindow = document.getElementById('chat-window');
const chatClose = document.getElementById('chat-close');
const messagesContainer = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');

// Toggle chat window
chatToggle.addEventListener('click', () => {
    chatWindow.classList.toggle('hidden');
});

chatClose.addEventListener('click', () => {
    chatWindow.classList.add('hidden');
});

// Send message
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage(message, 'user');
    messageInput.value = '';
    
    // Show typing indicator
    const typingId = addTypingIndicator();

    try {
        const response = await fetch(`/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                conversation_id: conversationId
            })
        });

        const data = await response.json();
        conversationId = data.conversation_id;

        // Remove typing indicator
        removeTypingIndicator(typingId);

        // Add bot response
        addMessage(data.response, 'bot');

        // Show lead score if available
        if (data.lead_score) {
            addMessage(`📊 Lead Score: ${data.lead_score}/100`, 'bot');
        }

        // Show captured data
        if (data.lead_data && Object.values(data.lead_data).some(v => v)) {
            const leadInfo = Object.entries(data.lead_data)
                .filter(([_, v]) => v)
                .map(([k, v]) => `${k}: ${v}`)
                .join('\n');
            addMessage(`📝 Captured:\n${leadInfo}`, 'bot');
        }

    } catch (error) {
        removeTypingIndicator(typingId);
        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        console.error('Error:', error);
    }
}

function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    messageDiv.textContent = text;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addTypingIndicator() {
    const id = Date.now();
    const div = document.createElement('div');
    div.id = `typing-${id}`;
    div.className = 'message bot';
    div.textContent = '...';
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const element = document.getElementById(`typing-${id}`);
    if (element) element.remove();
}

// Event listeners
sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// Open chat with welcome message
chatToggle.click();