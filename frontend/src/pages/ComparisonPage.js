import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import ResultPage from './ResultPage';
import { imageService, authService } from '../services/api';
import '../assets/styles/Comparison.css';

const ComparisonPage = ({ project = null, onBack = null }) => {
  const [image1, setImage1] = useState(null);
  const [image2, setImage2] = useState(null);
  const [compareUrl, setCompareUrl] = useState('');
  const [title, setTitle] = useState('');
  const [preview1, setPreview1] = useState(null);
  const [preview2, setPreview2] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [compareMode, setCompareMode] = useState('upload');
  
  // ✅ THÊM STATE CHO SIDEBAR
  const [projectHistory, setProjectHistory] = useState([]);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);

  // ✅ LOAD LỊCH SỬ KHI VÀO TRANG
  useEffect(() => {
    if (project?.id) {
      loadProjectHistory();
    }
  }, [project]);

  const loadProjectHistory = async () => {
    try {
      const response = await imageService.getProjectComparisons(project.id);
      setProjectHistory(response.comparisons);
    } catch (err) {
      console.error('Lỗi tải lịch sử:', err);
    }
  };

  // ✅ XỬ LÝ CLICK VÀO LỊCH SỬ
  const handleHistoryClick = (historyItem) => {
    setSelectedHistoryItem(historyItem);
    setResult({
      ...historyItem,
      comparison_id: historyItem.id,
      project: project
    });
  };

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

  const handleStatusUpdate = (comparisonId, newStatus) => {
    setProjectHistory(prevHistory => 
      prevHistory.map(item => 
        item.id === comparisonId 
          ? { ...item, status: newStatus, updated_at: new Date().toISOString() }
          : item
      )
    );
    
    if (selectedHistoryItem && selectedHistoryItem.id === comparisonId) {
      setSelectedHistoryItem(prev => ({
        ...prev,
        status: newStatus,
        updated_at: new Date().toISOString()
      }));
      
      setResult(prev => ({
        ...prev,
        status: newStatus,
        updated_at: new Date().toISOString()
      }));
    }
  };

  const handleCompareImages = async (e) => {
    e.preventDefault();
    
    if (!image1) {
      setError('Vui lòng upload ảnh đầu tiên');
      return;
    }

    if (!title.trim()) {  
      setError('Vui lòng nhập tiêu đề so sánh');
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

    const currentUser = authService.getCurrentUser();
    if (!currentUser) {
      setError('Vui lòng đăng nhập để so sánh');
      return;
    }

    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      let result;
      
      if (compareMode === 'upload') {
        result = await imageService.compareImages(
          image1, image2, title.trim(), currentUser.id, project?.id || null 
        );
      } else {
        result = await imageService.compareWithUrl(
          image1, compareUrl.trim(), title.trim(), currentUser.id, project?.id || null
        );
      }
      
      if (project) {
        result.project = project;
      }
      
      setResult(result);
      loadProjectHistory();

      setTitle('');
      setImage1(null);
      setImage2(null);
      setCompareUrl('');
      setPreview1(null);
      setPreview2(null);
    } catch (err) {
      setError(err.message || 'Có lỗi xảy ra khi so sánh');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseError = () => setError('');
  const handleBackFromResult = () => {
    setResult(null);
    setSelectedHistoryItem(null);
  };

  const isValidToCompare = image1 && !isLoading && 
    (compareMode === 'upload' ? image2 : compareUrl.trim());

  if (result) {
    return <ResultPage result={result} onBack={handleBackFromResult} onStatusUpdate={handleStatusUpdate} />;
  }

  return (
    <div className="comparison-page-with-sidebar">
      <div className="container">
        {/* ✅ SIDEBAR LỊCH SỬ */}
        {project && (
          <div className="history-sidebar">
            <h3>📚 Lịch sử so sánh</h3>
            <div className="history-list">
              {projectHistory.length === 0 ? (
                <p className="no-history">Chưa có lịch sử so sánh</p>
              ) : (
                projectHistory.map((item) => (
                  <div 
                    key={item.id} 
                    className={`history-item ${selectedHistoryItem?.id === item.id ? 'active' : ''}`}
                    onClick={() => handleHistoryClick(item)}
                  >
                    <img 
                      src={item.image1_url} 
                      alt="Ảnh gốc" 
                      className="history-thumbnail"
                    />
                    <div className="history-info">
                      <div className="history-title">{item.title}</div>  
                      <div className="history-score">{item.similarity_score}%</div>
                      <div className="history-date">
                        {new Date(item.created_at).toLocaleDateString()}
                      </div>
                      <div className={`history-status status-${item.status}`}>
                        {getStatusIcon(item.status)} {item.status.toUpperCase()}
                      </div>  
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* ✅ MAIN CONTENT */}
        <div className="main-content">
          {project && (
            <div className="project-context">
              <div className="project-info">
                <h2>📁 Project: {project.name}</h2>
                <p>{project.description || 'Không có mô tả'}</p>
              </div>
              {onBack && (
                <button onClick={onBack} className="back-btn">
                  ← Quay lại Projects
                </button>
              )}
            </div>
          )}

          <div className="image-upload-container">
            <h1 className="title">🔍 So sánh ảnh mới</h1>

            <div className="title-section">
              <h3>📝 Tiêu đề so sánh:</h3>
              <input
                type="text"
                placeholder="Nhập tiêu đề cho lần so sánh này (VD: Header Homepage - Test 1)"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                disabled={isLoading}
                className="title-input"
                maxLength="255"
              />
            </div>
            
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
                  </div>
                )}
              </div>
              
              <button
                type="submit"
                className="compare-btn"
                disabled={!title.trim() || !image1 || isLoading || 
                  (compareMode === 'upload' ? !image2 : !compareUrl.trim())}
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
        </div>
      </div>
    </div>
  );
};

const getStatusIcon = (status) => {
  switch (status) {
    case 'pass': return '✅';
    case 'fail': return '❌';
    case 'retest': return '🔄';
    case 'blocked': return '🚫';
    case 'pending': return '⏳';
    default: return '❓';
  }
};

export default ComparisonPage;