import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Brain } from 'lucide-react';
import MessageBubble from './MessageBubble';

const API_URL = "http://localhost:8000/api";

const ChatInterface = () => {
    const [messages, setMessages] = useState([
        { text: "**MTG Judge AI**: Ready for your questions. Ask about rules, prices, or versions!", isUser: false }
    ]);
    const [inputValue, setInputValue] = useState("");
    const [smartMode, setSmartMode] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    // History tracking for context
    const [history, setHistory] = useState([]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userText = inputValue.trim();
        setInputValue("");

        // Add user message
        const newMessages = [...messages, { text: userText, isUser: true }];
        setMessages(newMessages);
        setIsLoading(true);

        try {
            const payload = {
                query: userText,
                history: history,
                smart_mode: smartMode,
                context: null // We could persist context here if needed
            };

            const response = await fetch(`${API_URL}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) throw new Error(data.detail || "Error fetching response");

            setMessages(prev => [...prev, {
                text: data.response,
                isUser: false,
                model: smartMode ? "smart" : "fast",
                queryContext: userText
            }]);

            // Update history (keep last 8 interactions)
            const newHistory = [...history, userText, data.response];
            if (newHistory.length > 8) newHistory.splice(0, newHistory.length - 8);
            setHistory(newHistory);

        } catch (error) {
            console.error("Chat Error:", error);
            setMessages(prev => [...prev, { text: "⚠️ Error: Could not reach the Judge. Is the backend running?", isUser: false }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const handleFeedback = async (messageObject, rating) => {
        try {
            await fetch(`${API_URL}/feedback`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: messageObject.queryContext || "Unknown",
                    response: messageObject.text,
                    rating: rating,
                    model: messageObject.model || "unknown"
                })
            });
            console.log("Feedback sent!");
        } catch (e) {
            console.error("Feedback error", e);
        }
    };

    const handleReport = async (messageObject, comment) => {
        try {
            await fetch(`${API_URL}/report`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: messageObject.queryContext || "Unknown",
                    response: messageObject.text,
                    comment: comment,
                    model: messageObject.model || "unknown"
                })
            });
            console.log("Report sent!");
        } catch (e) {
            console.error("Report error", e);
        }
    };

    return (
        <div className="chat-container">
            <div className="messages-area">
                {messages.map((msg, idx) => (
                    <MessageBubble
                        key={idx}
                        message={msg}
                        isUser={msg.isUser}
                        onFeedback={!msg.isUser ? (r) => handleFeedback(msg, r) : null}
                        onReport={!msg.isUser ? (c) => handleReport(msg, c) : null}
                    />
                ))}
                {isLoading && (
                    <div className="message ai">
                        <div className="typing-dots">
                            <span></span><span></span><span></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="input-area">
                <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask a rule question or check a price..."
                    disabled={isLoading}
                    rows={1}
                />

                <div className="controls">
                    <div
                        className={`model-toggle ${smartMode ? 'active' : ''}`}
                        onClick={() => setSmartMode(!smartMode)}
                        title="Toggle between Fast Mode and Smart Mode (70B)"
                    >
                        <div className="toggle-switch"></div>
                        <span className="toggle-label">
                            {smartMode ? "Smart Mode" : "Fast Mode"}
                        </span>
                    </div>

                    <button
                        className="send-btn"
                        onClick={handleSendMessage}
                        disabled={isLoading || !inputValue.trim()}
                    >
                        <Send size={24} strokeWidth={2.5} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;
