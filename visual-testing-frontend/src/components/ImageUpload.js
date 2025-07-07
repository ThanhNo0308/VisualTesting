import React, { useState } from 'react';
import '../styles/ImageUpload.css';

const ImageUpload = ({ onCompare, isLoading }) => {
  const [image1, setImage1] = useState(null);
  const [image2, setImage2] = useState(null);
  const [preview1, setPreview1] = useState(null);
  const [preview2, setPreview2] = useState(null);

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

  const handleSubmit = (e) => {
    e.preventDefault();
    if (image1 && image2) {
      onCompare(image1, image2);
    }
  };

  const isValidToCompare = image1 && image2 && !isLoading;

  return (
    <div className="image-upload-container">
      <h1 className="title">🔍 So sánh ảnh bằng SSIM</h1>
      
      <form onSubmit={handleSubmit} className="upload-form">
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
  );
};

export default ImageUpload;