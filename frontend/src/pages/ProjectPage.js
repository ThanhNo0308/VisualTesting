import React, { useState, useEffect } from 'react';
import { projectService, authService } from '../services/api';
import ComparisonPage from './ComparisonPage';
import ErrorMessage from '../components/ErrorMessage';
import LoadingSpinner from '../components/LoadingSpinner';
import '../assets/styles/ProjectPage.css';

const ProjectPage = () => {
  const [projects, setProjects] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    figma_url: ''
  });

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      
      const currentUser = authService.getCurrentUser();
      if (!currentUser) {
        setError('Vui lòng đăng nhập');
        return;
      }
      
      // ✅ LẤY PROJECT THEO USER
      const response = await projectService.getProjects(currentUser.id);
      setProjects(response.projects);
      
    } catch (err) {
      setError(err.message || 'Không thể tải danh sách projects');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      setError('Tên project không được trống');
      return;
    }

    try {
      setIsLoading(true);
      
      const currentUser = authService.getCurrentUser();
      if (!currentUser) {
        setError('Vui lòng đăng nhập để tạo project');
        return;
      }
      
      await projectService.createProject(formData, currentUser.id);
      
      setShowCreateForm(false);
      setFormData({ name: '', description: '', figma_url: '' });
      loadProjects();
      
    } catch (err) {
      setError(err.message || 'Lỗi tạo project');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  // ✅ XỬ LÝ CLICK SO SÁNH
  const handleCompareClick = (project) => {
    setSelectedProject(project);
    setShowComparison(true);
  };

  // ✅ XỬ LÝ QUAY LẠI TỪ COMPARISON
  const handleBackFromComparison = () => {
    setShowComparison(false);
    setSelectedProject(null);
  };

  // ✅ XỬ LÝ XÓA PROJECT
  const handleDeleteProject = async (projectId) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa project này?')) {
      return;
    }

    try {
      setIsLoading(true);
      
      const currentUser = authService.getCurrentUser();
      if (!currentUser) {
        setError('Vui lòng đăng nhập');
        return;
      }
      
      await projectService.deleteProject(projectId, currentUser.id);
      loadProjects();
      
    } catch (err) {
      setError(err.message || 'Lỗi xóa project');
    } finally {
      setIsLoading(false);
    }
  };

  // ✅ HIỂN THỊ COMPARISON PAGE
  if (showComparison) {
    return (
      <ComparisonPage 
        project={selectedProject}
        onBack={handleBackFromComparison}
      />
    );
  }

  return (
    <div className="project-page">
      <div className="container">
        <div className="project-header">
          <h1>📁 Quản lý Projects</h1>
          <button 
            className="create-btn"
            onClick={() => setShowCreateForm(!showCreateForm)}
          >
            {showCreateForm ? '❌ Hủy' : '➕ Tạo Project'}
          </button>
        </div>

        {showCreateForm && (
          <div className="create-form-container">
            <h2>🆕 Tạo Project mới</h2>
            <form onSubmit={handleCreateProject} className="create-form">
              <div className="form-group">
                <label>Tên Project *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="Nhập tên project"
                  required
                />
              </div>

              <div className="form-group">
                <label>Mô tả</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="Mô tả project (không bắt buộc)"
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label>Figma URL</label>
                <input
                  type="url"
                  name="figma_url"
                  value={formData.figma_url}
                  onChange={handleInputChange}
                  placeholder="https://figma.com/..."
                />
              </div>

              <div className="form-actions">
                <button type="submit" className="submit-btn" disabled={isLoading}>
                  {isLoading ? '🔄 Đang tạo...' : '✅ Tạo Project'}
                </button>
                <button 
                  type="button" 
                  className="cancel-btn"
                  onClick={() => setShowCreateForm(false)}
                >
                  Hủy
                </button>
              </div>
            </form>
          </div>
        )}

        <ErrorMessage 
          message={error}
          onClose={() => setError('')}
        />

        {isLoading && <LoadingSpinner message="Đang tải..." />}

        <div className="projects-grid">
          {projects.length === 0 ? (
            <div className="no-projects">
              <p>📂 Chưa có project nào</p>
              <p>Tạo project đầu tiên để bắt đầu!</p>
            </div>
          ) : (
            projects.map((project) => (
              <div key={project.id} className="project-card">
                <h3>{project.name}</h3>
                <p className="project-description">
                  {project.description || 'Chưa có mô tả'}
                </p>
                {project.figma_url && (
                  <a 
                    href={project.figma_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="figma-link"
                  >
                    🎨 Xem Figma
                  </a>
                )}
                <div className="project-meta">
                  <span>📅 {new Date(project.created_at).toLocaleDateString()}</span>
                </div>
                <div className="project-actions">
                  <button 
                    className="action-btn detail-btn"
                    onClick={() => alert(`Chi tiết project: ${project.name}`)}
                  >
                    📊 Xem chi tiết
                  </button>
                  <button 
                    className="action-btn compare-btn"
                    onClick={() => handleCompareClick(project)}
                  >
                    🔄 So sánh
                  </button>
                  <button 
                    className="action-btn delete-btn"
                    onClick={() => handleDeleteProject(project.id)}
                  >
                    🗑️ Xóa
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectPage;