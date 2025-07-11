import React from 'react';
import '../assets/styles/LoadingSpinner.css';

const LoadingSpinner = ({ message = 'Đang xử lý...' }) => {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p className="loading-message">⏳ {message}</p>
    </div>
  );
};

export default LoadingSpinner;