import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

export const imageService = {
  compareImages: async (image1, image2, userId, projectId = null) => {
    const formData = new FormData();
    formData.append('image1', image1);
    formData.append('image2', image2);
    formData.append('user_id', userId);
    
    if (projectId) {
      formData.append('project_id', projectId);
    }

    try {
      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Lỗi kết nối server');
    }
  },

  compareWithUrl: async (templateImage, url, userId, projectId = null) => {
    const formData = new FormData();
    formData.append('image1', templateImage);
    formData.append('compare_url', url);
    formData.append('user_id', userId);
    
    if (projectId) {
      formData.append('project_id', projectId);
    }

    try {
      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Lỗi template matching');
    }
  },

  getUserComparisons: async (userId) => {
    try {
      const response = await api.get(`/users/${userId}/comparisons`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Lỗi lấy lịch sử so sánh');
    }
  },

  deleteComparison: async (comparisonId, userId) => {
    try {
      const response = await api.delete(`/comparisons/${comparisonId}?user_id=${userId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Lỗi xóa comparison');
    }
  },

  getImageUrl: (filename) => {
    if (filename && (filename.startsWith('http') || filename.startsWith('https'))) {
      return filename;
    }
    return filename;
  },

  getCloudinaryUrl: (url) => {
    return url;
  }
};

export const projectService = {
  createProject: async (projectData, ownerId) => {
    try {
      const formData = new FormData();
      formData.append('name', projectData.name);
      formData.append('description', projectData.description || '');
      formData.append('figma_url', projectData.figma_url || '');
      formData.append('owner_id', ownerId);
      
      const response = await api.post('/projects', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Lỗi tạo project');
    }
  },

  getProjects: async (userId) => {
    try {
      const response = await api.get(`/users/${userId}/projects`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Lỗi lấy projects');
    }
  },

  deleteProject: async (projectId, userId) => {
    try {
      const response = await api.delete(`/projects/${projectId}?user_id=${userId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Lỗi xóa project');
    }
  },
};

export const authService = {
  register: async (userData) => {
    try {
      const response = await api.post('/register', userData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Lỗi đăng ký');
    }
  },

  login: async (credentials) => {
    try {
      const response = await api.post('/login', credentials);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Lỗi đăng nhập');
    }
  },

  logout: () => {
    localStorage.removeItem('user');
  },

  getCurrentUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },
};