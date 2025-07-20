import React from 'react';
import '../assets/styles/Header.css';
import iconImage from '../assets/images/icon.png';

const Header = ({ user, onLogout }) => {
  return (
    <header className="app-header">
      <div className="header-content">
        <div className="logo-section">
          <img src={iconImage} alt="Visual Testing" className="logo-icon" />
          <h1 className="app-title">Visual Testing Platform</h1>
        </div>
        
        {user && (
          <div className="user-section">
            <div className="user-info">
              <div className="user-avatar">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <span>Xin chào, {user.name}</span>
            </div>
            <button onClick={onLogout} className="logout-btn">
              Đăng xuất
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;