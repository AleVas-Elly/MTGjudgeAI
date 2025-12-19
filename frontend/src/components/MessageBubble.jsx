import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ThumbsUp, ThumbsDown, Flag } from 'lucide-react';

const MessageBubble = ({ message, isUser, onFeedback, onReport }) => {
    const [feedback, setFeedback] = useState(null); // 'up' | 'down' | null
    const [isReporting, setIsReporting] = useState(false);
    const [reportText, setReportText] = useState("");

    const handleFeedback = (rating) => {
        setFeedback(rating);
        if (onFeedback) onFeedback(message, rating);
    };

    const submitReport = () => {
        if (onReport && reportText.trim()) {
            onReport(message, reportText);
            setIsReporting(false);
            setReportText("");
            alert("Report sent! Thank you.");
        }
    };

    return (
        <div className={`message ${isUser ? 'user' : 'ai'}`}>
            <div className="content">
                {isUser ? (
                    <p>{message.text}</p>
                ) : (
                    <ReactMarkdown>{message.text}</ReactMarkdown>
                )}
            </div>

            {/* Reporting Form */}
            {isReporting && (
                <div className="report-form" style={{ marginTop: '10px', background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '8px' }}>
                    <textarea
                        value={reportText}
                        onChange={(e) => setReportText(e.target.value)}
                        placeholder="Describe the problem..."
                        style={{ width: '100%', background: '#0f1115', color: '#fff', border: '1px solid #334155', borderRadius: '4px', padding: '5px' }}
                    />
                    <div style={{ display: 'flex', gap: '5px', marginTop: '5px', justifyContent: 'flex-end' }}>
                        <button onClick={() => setIsReporting(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>Cancel</button>
                        <button onClick={submitReport} style={{ background: '#ef4444', border: 'none', color: 'white', padding: '4px 8px', borderRadius: '4px', cursor: 'pointer' }}>Submit</button>
                    </div>
                </div>
            )}

            {!isUser && !isReporting && (
                <div className="feedback-actions">
                    <button
                        className={`feedback-btn ${feedback === 'up' ? 'active' : ''}`}
                        onClick={() => handleFeedback('up')}
                        title="Good answer"
                    >
                        <ThumbsUp size={14} />
                    </button>
                    <button
                        className={`feedback-btn ${feedback === 'down' ? 'active down' : ''}`}
                        onClick={() => handleFeedback('down')}
                        title="Bad answer"
                    >
                        <ThumbsDown size={14} />
                    </button>
                    <button
                        className="feedback-btn"
                        onClick={() => setIsReporting(true)}
                        title="Report a problem"
                    >
                        <Flag size={14} />
                    </button>
                </div>
            )}
        </div>
    );
};

export default MessageBubble;
