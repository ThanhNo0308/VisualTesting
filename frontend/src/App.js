import React, { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import ProjectPage from './pages/ProjectPage';
import { authService } from './services/api';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Kiểm tra user đã đăng nhập chưa
    const savedUser = authService.getCurrentUser();
    if (savedUser) {
      setUser(savedUser);
    }
    setIsLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
  };

  if (isLoading) {
    return (
      <div className="app-loading">
        <div className="spinner"></div>
        <p>Đang tải...</p>
      </div>
    );
  }

  return (
    <div className="app">
      {!user ? (
        <LoginPage onLogin={handleLogin} />
      ) : (
        <div>
          <div className="app-header">
            <h1>🔍 Visual Testing</h1>
            <div className="user-info">
              <span>Xin chào, {user.name}!</span>
              <button onClick={handleLogout} className="logout-btn">
                🚪 Đăng xuất
              </button>
            </div>
          </div>
          <ProjectPage />
        </div>
      )}
    </div>
  );
}

export default App;