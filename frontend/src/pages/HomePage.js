import React, { useState } from 'react';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import ResultPage from '../pages/ResultPage';
import { imageService } from '../services/api';
import '../assets/styles/HomePage.css';

const HomePage = () => {
  const [image1, setImage1] = useState(null);
  const [image2, setImage2] = useState(null);
  const [compareUrl, setCompareUrl] = useState('');
  const [preview1, setPreview1] = useState(null);
  const [preview2, setPreview2] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [compareMode, setCompareMode] = useState('upload');

  const handleImageChange = (imageFile, imageNumber) => {
    if (imageFile) {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (imageNumber === 1) {
          setImage1(imageFile);
          setPreview1(e.target.result);
        } else {
          setImage2(imageFile);
          setPreview2(e.target.result);
        }
      };
      reader.readAsDataURL(imageFile);
    }
  };

  const handleCompareImages = async (e) => {
    e.preventDefault();
    
    if (!image1) {
      setError('Vui lòng upload ảnh đầu tiên');
      return;
    }

    if (compareMode === 'upload' && !image2) {
      setError('Vui lòng upload ảnh thứ hai');
      return;
    }

    if (compareMode === 'url' && !compareUrl.trim()) {
      setError('Vui lòng nhập URL để so sánh');
      return;
    }

    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      let result;
      
      if (compareMode === 'upload') {
        result = await imageService.compareImages(image1, image2);
      } else {
        result = await imageService.compareWithUrl(image1, compareUrl.trim());
      }
      
      setResult(result);
    } catch (err) {
      setError(err.message || 'Có lỗi xảy ra khi so sánh');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseError = () => {
    setError('');
  };

  const isValidToCompare = image1 && !isLoading && 
    (compareMode === 'upload' ? image2 : compareUrl.trim());

  return (
    <div className="home-page">
      <div className="container">
        <div className="image-upload-container">
          <h1 className="title">🔍 So sánh ảnh thông minh</h1>
          
          {/* Phần chọn chế độ so sánh */}
          <div className="compare-mode-section">
            <h3>🎯 Chọn phương thức so sánh:</h3>
            <div className="mode-buttons">
              <button
                type="button"
                className={`mode-btn ${compareMode === 'upload' ? 'active' : ''}`}
                onClick={() => setCompareMode('upload')}
                disabled={isLoading}
              >
                📁 Upload 2 ảnh
              </button>
              <button
                type="button"
                className={`mode-btn ${compareMode === 'url' ? 'active' : ''}`}
                onClick={() => setCompareMode('url')}
                disabled={isLoading}
              >
                🌐 Template Matching với URL
              </button>
            </div>
          </div>
          
          {/* Form upload */}
          <form onSubmit={handleCompareImages} className="upload-form">
            <div className="upload-section">
              <div className="upload-box">
                <h3>
                  {compareMode === 'upload' ? '📷 Ảnh gốc (Baseline)' : '🎯 Ảnh thiết kế (Template)'}
                </h3>
                <p className="description">
                  {compareMode === 'upload' 
                    ? 'Upload ảnh baseline để so sánh'
                    : 'Upload ảnh quảng cáo/banner cần tìm trên website'
                  }
                </p>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleImageChange(e.target.files[0], 1)}
                  required
                  disabled={isLoading}
                />
                {preview1 && (
                  <div className="preview-container">
                    <img src={preview1} alt="Preview 1" className="preview-img" />
                  </div>
                )}
              </div>
              
              {compareMode === 'upload' ? (
                <div className="upload-box">
                  <h3>🔍 Ảnh so sánh</h3>
                  <p className="description">Upload ảnh thứ hai để so sánh với ảnh gốc</p>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleImageChange(e.target.files[0], 2)}
                    required
                    disabled={isLoading}
                  />
                  {preview2 && (
                    <div className="preview-container">
                      <img src={preview2} alt="Preview 2" className="preview-img" />
                    </div>
                  )}
                </div>
              ) : (
                <div className="upload-box url-input-box">
                  <h3>🌐 URL trang web</h3>
                  <p className="description">
                    Nhập URL trang web có chứa banner/quảng cáo cần kiểm tra
                  </p>
                  <input
                    type="url"
                    placeholder="https://example.com"
                    value={compareUrl}
                    onChange={(e) => setCompareUrl(e.target.value)}
                    required
                    disabled={isLoading}
                    className="url-input"
                  />
                  <div className="template-info">
                    <h4>💡 Cách hoạt động:</h4>
                    <ul>
                      <li>🔍 Hệ thống sẽ chụp toàn bộ trang web</li>
                      <li>🎯 Tìm kiếm banner/quảng cáo trên trang</li>
                      <li>✂️ Cắt chính xác vùng tìm thấy</li>
                      <li>📊 So sánh với ảnh thiết kế đã upload</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
            
            <button
              type="submit"
              className="compare-btn"
              disabled={!isValidToCompare}
            >
              {isLoading 
                ? (compareMode === 'upload' ? '🔄 Đang so sánh...' : '🔄 Đang tìm và so sánh...')
                : (compareMode === 'upload' ? '🔄 So sánh ảnh' : '🎯 Tìm và so sánh Banner')
              }
            </button>
          </form>
        </div>
        
        {isLoading && (
          <LoadingSpinner 
            message={
              compareMode === 'upload' 
                ? "Đang so sánh ảnh, vui lòng đợi..." 
                : "Đang chụp trang web và tìm banner..."
            } 
          />
        )}
        
        <ErrorMessage 
          message={error}
          onClose={handleCloseError}
        />
        
        {result && <ResultPage result={result} />}
      </div>
    </div>
  );
};

export default HomePage;