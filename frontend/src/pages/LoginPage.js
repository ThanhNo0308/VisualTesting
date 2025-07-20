import React, { useState } from 'react';
import { authService } from '../services/api';
import ErrorMessage from '../components/ErrorMessage';
import LoadingSpinner from '../components/LoadingSpinner';
import '../assets/styles/LoginPage.css';

const AuthPage = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: ''
  });

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!formData.email || !formData.password) {
      setError('Vui lòng nhập đầy đủ thông tin');
      return;
    }

    if (!isLogin && !formData.name) {
      setError('Vui lòng nhập tên');
      return;
    }

    try {
      setIsLoading(true);
      
      if (isLogin) {
        const response = await authService.login({
          email: formData.email,
          password: formData.password
        });
        
        // Lưu thông tin user vào localStorage
        localStorage.setItem('user', JSON.stringify(response.user));
        onLogin(response.user);
      } else {
        const response = await authService.register({
          name: formData.name,
          email: formData.email,
          password: formData.password
        });
        
        // Tự động chuyển sang đăng nhập
        setIsLogin(true);
        setFormData({ name: '', email: '', password: '' });
        setError('');
        alert('Đăng ký thành công! Vui lòng đăng nhập.');
      }
    } catch (err) {
      setError(err.message || 'Có lỗi xảy ra');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setFormData({ name: '', email: '', password: '' });
    setError('');
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1>🔍 Visual Testing</h1>
          <h2>{isLogin ? '👤 Đăng nhập' : '📝 Đăng ký'}</h2>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {!isLogin && (
            <div className="form-group">
              <label>Tên *</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Nhập tên của bạn"
                required={!isLogin}
              />
            </div>
          )}

          <div className="form-group">
            <label>Email *</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="Nhập email"
              required
            />
          </div>

          <div className="form-group">
            <label>Mật khẩu *</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder="Nhập mật khẩu"
              required
            />
          </div>

          <button type="submit" className="auth-btn" disabled={isLoading}>
            {isLoading ? '⏳ Đang xử lý...' : 
             isLogin ? '🔐 Đăng nhập' : '📝 Đăng ký'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            {isLogin ? 'Chưa có tài khoản?' : 'Đã có tài khoản?'}
            <button type="button" className="toggle-btn" onClick={toggleMode}>
              {isLogin ? 'Đăng ký ngay' : 'Đăng nhập'}
            </button>
          </p>
        </div>

        <ErrorMessage 
          message={error}
          onClose={() => setError('')}
        />

        {isLoading && <LoadingSpinner message="Đang xử lý..." />}
      </div>
    </div>
  );
};

export default AuthPage;