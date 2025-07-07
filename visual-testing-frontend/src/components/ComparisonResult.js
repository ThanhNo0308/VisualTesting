import React, { useState } from 'react';
import { imageService } from '../services/api';
import '../styles/ComparisonResult.css';

const ComparisonResult = ({ result }) => {
  const [showHeatmap, setShowHeatmap] = useState(false);

  if (!result) return null;

  const getScoreClass = (score) => {
    if (score >= 95) return 'score-high';
    if (score >= 80) return 'score-medium';
    return 'score-low';
  };

  const getScoreText = (score) => {
    if (score >= 95) return 'Rất giống nhau';
    if (score >= 80) return 'Khá giống nhau';
    return 'Khác biệt nhiều';
  };

  const getDifferencesByLevel = () => {
    if (!result.difference_details) return { high: 0, medium: 0, low: 0 };
    
    return result.difference_details.reduce((acc, diff) => {
      acc[diff.level] = (acc[diff.level] || 0) + 1;
      return acc;
    }, { high: 0, medium: 0, low: 0 });
  };

  const diffLevels = getDifferencesByLevel();

  return (
    <div className="result-container">
      <h2 className="result-title">📊 Kết quả so sánh chi tiết</h2>
      
      <div className={`similarity-score ${getScoreClass(result.similarity_score)}`}>
        <div className="score-value">
          Độ tương đồng: {result.similarity_score}%
        </div>
        <div className="score-description">
          {getScoreText(result.similarity_score)}
        </div>
      </div>
      
      {/* Thống kê chi tiết */}
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

      {/* Phân loại khác biệt theo mức độ */}
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
      
      {/* Toggle heatmap */}
      {result.heatmap_image && (
        <div className="heatmap-toggle">
          <button 
            className="toggle-btn"
            onClick={() => setShowHeatmap(!showHeatmap)}
          >
            {showHeatmap ? '📊 Ẩn Heatmap' : '🔥 Hiện Heatmap'}
          </button>
        </div>
      )}
      
      <div className="result-grid">
        <div className="result-item">
          <h3>Ảnh gốc</h3>
          <img
            src={imageService.getImageUrl(result.image1_path)}
            alt="Ảnh gốc"
            className="result-image"
          />
        </div>
        
        <div className="result-item">
          <h3>Ảnh so sánh</h3>
          <img
            src={imageService.getImageUrl(result.image2_path)}
            alt="Ảnh so sánh"
            className="result-image"
          />
        </div>
        
        <div className="result-item">
          <h3>
            {showHeatmap ? 'Heatmap khác biệt' : 'Kết quả (Highlight khác biệt)'}
          </h3>
          <img
            src={showHeatmap && result.heatmap_image 
              ? imageService.getImageUrl(result.heatmap_image, 'results')
              : imageService.getImageUrl(result.result_image, 'results')
            }
            alt={showHeatmap ? 'Heatmap' : 'Kết quả so sánh'}
            className="result-image"
          />
        </div>
      </div>

      {/* Chi tiết từng vùng khác biệt */}
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
            {result.difference_details.slice(0, 10).map((detail, index) => (
              <div key={index} className={`table-row ${detail.level}`}>
                <span>({detail.x}, {detail.y})</span>
                <span>{detail.width} × {detail.height}</span>
                <span>{detail.area} px</span>
                <span className={`level-badge ${detail.level}`}>
                  {detail.level === 'high' ? 'Cao' : 
                   detail.level === 'medium' ? 'Trung bình' : 'Thấp'}
                </span>
                <span>{detail.avg_difference.toFixed(1)}</span>
              </div>
            ))}
            {result.difference_details.length > 10 && (
              <div className="table-footer">
                ... và {result.difference_details.length - 10} vùng khác biệt khác
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ComparisonResult;