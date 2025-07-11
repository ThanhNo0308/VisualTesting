import React, { useState } from 'react';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import ResultPage from '../pages/ResultPage';
import { imageService } from '../services/api';
import '../assets/styles/HomePage.css';

const HomePage = () => {
  const [image1, setImage1] = useState(null);
  const [image2, setImage2] = useState(null);
  const [preview1, setPreview1] = useState(null);
  const [preview2, setPreview2] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

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
    if (!image1 || !image2) return;

    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const ResultPage = await imageService.compareImages(image1, image2);
      setResult(ResultPage);
    } catch (err) {
      setError(err.message || 'Có lỗi xảy ra khi so sánh ảnh');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseError = () => {
    setError('');
  };

  const isValidToCompare = image1 && image2 && !isLoading;

  return (
    <div className="home-page">
      <div className="container">
        <div className="image-upload-container">
          <h1 className="title">🔍 So sánh ảnh bằng SSIM</h1>
          
          <form onSubmit={handleCompareImages} className="upload-form">
            <div className="upload-section">
              <div className="upload-box">
                <h3>Ảnh gốc (Baseline)</h3>
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
              
              <div className="upload-box">
                <h3>Ảnh so sánh</h3>
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
            </div>
            
            <button
              type="submit"
              className="compare-btn"
              disabled={!isValidToCompare}
            >
              {isLoading ? '🔄 Đang so sánh...' : '🔄 So sánh ảnh'}
            </button>
          </form>
        </div>
        
        {isLoading && (
          <LoadingSpinner message="Đang so sánh ảnh, vui lòng đợi..." />
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