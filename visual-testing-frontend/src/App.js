import React, { useState } from 'react';
import ImageUpload from './components/ImageUpload';
import ComparisonResult from './components/ComparisonResult';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorMessage from './components/ErrorMessage';
import { imageService } from './services/api';
import './App.css';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleCompareImages = async (image1, image2) => {
    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const comparisonResult = await imageService.compareImages(image1, image2);
      setResult(comparisonResult);
    } catch (err) {
      setError(err.message || 'Có lỗi xảy ra khi so sánh ảnh');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseError = () => {
    setError('');
  };

  return (
    <div className="app">
      <div className="container">
        <ImageUpload 
          onCompare={handleCompareImages}
          isLoading={isLoading}
        />
        
        {isLoading && (
          <LoadingSpinner message="Đang so sánh ảnh, vui lòng đợi..." />
        )}
        
        <ErrorMessage 
          message={error}
          onClose={handleCloseError}
        />
        
        {result && <ComparisonResult result={result} />}
      </div>
    </div>
  );
}

export default App;