import React from 'react';
import '../styles/ErrorMessage.css';

const ErrorMessage = ({ message, onClose }) => {
  if (!message) return null;

  return (
    <div className="error-container">
      <div className="error-content">
        <span className="error-text">❌ {message}</span>
        {onClose && (
          <button className="error-close" onClick={onClose}>
            ✕
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorMessage;