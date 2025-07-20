import React, { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import ProjectPage from './pages/ProjectPage';
import Header from './components/Header';
import Footer from './components/Footer';
import { authService } from './services/api';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
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
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="app">
      {!user ? (
        <LoginPage onLogin={handleLogin} />
      ) : (
        <>
          <Header user={user} onLogout={handleLogout} />
          
          <main className="main-content">
            <ProjectPage />
          </main>

          <Footer />
        </>
      )}
    </div>
  );
}

export default App;