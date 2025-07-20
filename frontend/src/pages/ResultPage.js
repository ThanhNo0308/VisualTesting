import React, { useState } from 'react';
import { imageService } from '../services/api';
import ImageModal from '../components/ImageModal';
import '../assets/styles/ResultPage.css';

const ResultPage = ({ result, onBack }) => {
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [modalImage, setModalImage] = useState(null);
  const [modalTitle, setModalTitle] = useState('');

  const getScoreClass = (score) => {
    if (score >= 90) return 'excellent';
    if (score >= 70) return 'good';
    if (score >= 50) return 'fair';
    return 'poor';
  };

  const getScoreText = (score) => {
    if (score >= 90) return 'Tuyệt vời! Gần như giống hệt nhau';
    if (score >= 70) return 'Tốt! Có một số khác biệt nhỏ';
    if (score >= 50) return 'Khá! Có khác biệt đáng chú ý';
    return 'Kém! Có nhiều khác biệt lớn';
  };

  const openModal = (imageUrl, title) => {
    setModalImage(imageUrl);
    setModalTitle(title);
  };

  const closeModal = () => {
    setModalImage(null);
    setModalTitle('');
  };

  const diffLevels = {
    high: result.difference_details?.filter(d => d.level === 'high').length || 0,
    medium: result.difference_details?.filter(d => d.level === 'medium').length || 0,
    low: result.difference_details?.filter(d => d.level === 'low').length || 0,
  };

  const getImageSrc = (result, type) => {
    switch (type) {
      case 'image1':
        return result.image1_url || imageService.getImageUrl(result.image1_path);
      case 'image2':
        return result.image2_url || imageService.getImageUrl(result.image2_path);
      case 'result':
        return result.result_image_url || imageService.getImageUrl(result.result_image, 'results');
      case 'heatmap':
        return result.heatmap_image_url || imageService.getImageUrl(result.heatmap_image, 'results');
      default:
        return '';
    }
  };

  return (
    <div className="result-page">
      <div className="container">
        <div className="result-header">
          <h1>📊 Kết quả so sánh</h1>
          <button onClick={onBack} className="back-btn">
            ← Quay lại
          </button>
        </div>
        
        <div className={`similarity-score ${getScoreClass(result.similarity_score)}`}>
          <div className="score-value">
            Độ tương đồng: {result.similarity_score}%
          </div>
          <div className="score-description">
            {getScoreText(result.similarity_score)}
          </div>
        </div>
        
        <div className="analysis-details">
          <div className="analysis-item">
            <strong>Tổng số vùng khác biệt:</strong> {result.differences_count}
          </div>
          {result.analysis && (
            <>
              <div className="analysis-item">
                <strong>Tỷ lệ pixel khác biệt:</strong> {result.analysis.difference_percentage}%
              </div>
              <div className="analysis-item">
                <strong>Tổng số pixel:</strong> {result.analysis.total_pixels.toLocaleString()}
              </div>
            </>
          )}
        </div>

        {result.difference_details && (
          <div className="difference-levels">
            <h3>Phân loại khác biệt:</h3>
            <div className="levels-grid">
              <div className="level-item high">
                <span className="level-color"></span>
                <span>Khác biệt lớn: <strong>{diffLevels.high}</strong></span>
              </div>
              <div className="level-item medium">
                <span className="level-color"></span>
                <span>Khác biệt trung bình: <strong>{diffLevels.medium}</strong></span>
              </div>
              <div className="level-item low">
                <span className="level-color"></span>
                <span>Khác biệt nhỏ: <strong>{diffLevels.low}</strong></span>
              </div>
            </div>
          </div>
        )}
        
        {result.heatmap_image_url && (
          <div className="heatmap-toggle">
            <button 
              onClick={() => setShowHeatmap(!showHeatmap)}
              className="toggle-btn"
            >
              {showHeatmap ? '📊 Xem Highlight' : '🔥 Xem Heatmap'}
            </button>
          </div>
        )}

        <div className="result-images">
          <div className="result-item">
            <h3>Ảnh gốc</h3>
            <img
              src={getImageSrc(result, 'image1')}
              alt="Ảnh gốc"
              className="result-image clickable"
              onClick={() => openModal(
                getImageSrc(result, 'image1'),
                '📷 Ảnh gốc'
              )}
              title="Click để xem phóng to"
            />
          </div>
          
          <div className="result-item">
            <h3>Ảnh so sánh</h3>
            <img
              src={getImageSrc(result, 'image2')}
              alt="Ảnh so sánh"
              className="result-image clickable"
              onClick={() => openModal(
                getImageSrc(result, 'image2'),
                '🔍 Ảnh so sánh'
              )}
              title="Click để xem phóng to"
            />
          </div>
          
          <div className="result-item">
            <h3>
              {showHeatmap ? 'Heatmap khác biệt' : 'Kết quả (Highlight khác biệt)'}
            </h3>
            <img
              src={showHeatmap ? getImageSrc(result, 'heatmap') : getImageSrc(result, 'result')}
              alt={showHeatmap ? 'Heatmap' : 'Kết quả so sánh'}
              className="result-image clickable"
              onClick={() => openModal(
                showHeatmap ? getImageSrc(result, 'heatmap') : getImageSrc(result, 'result'),
                showHeatmap ? '🔥 Heatmap khác biệt' : '📊 Kết quả với highlight'
              )}
              title="Click để xem phóng to"
            />
          </div>
        </div>

        {result.difference_details && result.difference_details.length > 0 && (
          <div className="differences-details">
            <h3>Chi tiết các vùng khác biệt:</h3>
            <div className="details-table">
              <div className="table-header">
                <span>Vị trí (x, y)</span>
                <span>Kích thước</span>
                <span>Diện tích</span>
                <span>Mức độ</span>
                <span>Điểm khác biệt</span>
              </div>
              {result.difference_details.map((detail, index) => (
                <div key={index} className={`table-row ${detail.level}`}>
                  <span>({detail.x}, {detail.y})</span>
                  <span>{detail.width}x{detail.height}</span>
                  <span>{detail.area}px</span>
                  <span className={`level-badge ${detail.level}`}>
                    {detail.level}
                  </span>
                  <span>{detail.avg_difference.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <ImageModal
          isOpen={!!modalImage}
          imageUrl={modalImage}
          title={modalTitle}
          onClose={closeModal}
        />
      </div>
    </div>
  );
};

export default ResultPage;