import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000,
});

export const imageService = {
  compareImages: async (image1, image2, title, userId, projectId = null) => {
    try {
      const formData = new FormData();
      formData.append('image1', image1);
      formData.append('image2', image2);
      formData.append('title', title);
      formData.append('user_id', userId);
      if (projectId) formData.append('project_id', projectId);

      const response = await api.post('/upload', formData);
      return response.data;
    } catch (error) {
      console.error('❌ API compareImages error:', error.response?.data);
      throw error;
    }
  },

  compareWithUrl: async (templateImage, url, title, userId, projectId = null) => {
    try {
      const formData = new FormData();
      formData.append('image1', templateImage);
      formData.append('compare_url', url);
      formData.append('title', title);
      formData.append('user_id', userId);
      if (projectId) formData.append('project_id', projectId);

      const response = await api.post('/upload', formData);
      return response.data;
    } catch (error) {
      console.error('❌ API compareWithUrl error:', error.response?.data);
      throw error;
    }
  },

  updateComparisonStatus: async (comparisonId, status, userId) => {
  try {
    // ✅ FIX: VALIDATE INPUT
    if (!comparisonId || comparisonId === 'undefined') {
      throw new Error('Comparison ID không hợp lệ');
    }
    
    if (!status || !userId) {
      throw new Error('Thiếu thông tin status hoặc user ID');
    }

    console.log('📤 Sending status update:', { comparisonId, status, userId });

    const formData = new FormData();
    formData.append('status', status);
    formData.append('user_id', userId);
    
    const response = await api.patch(`/comparisons/${comparisonId}/status`, formData);
    return response.data;
  } catch (error) {
    console.error('❌ API updateComparisonStatus error:', error.response?.data || error.message);
    throw error;
  }
},

  getUserComparisons: async (userId) => {
    const response = await api.get(`/users/${userId}/comparisons`);
    return response.data;
  },

  getProjectComparisons: async (projectId) => {
    const response = await api.get(`/projects/${projectId}/comparisons`);
    return response.data;
  }
};

export const projectService = {
  createProject: async (projectData, ownerId) => {
    const formData = new FormData();
    formData.append('name', projectData.name);
    formData.append('description', projectData.description || '');
    formData.append('figma_url', projectData.figma_url || '');
    formData.append('owner_id', ownerId);
    
    const response = await api.post('/projects', formData);
    return response.data;
  },

  getProjects: async (userId) => {
    const response = await api.get(`/users/${userId}/projects`);
    return response.data;
  },

  deleteProject: async (projectId, userId) => {
    const response = await api.delete(`/projects/${projectId}?user_id=${userId}`);
    return response.data;
  }
};

export const authService = {
  register: async (userData) => {
    const response = await api.post('/register', userData);
    return response.data;
  },

  login: async (credentials) => {
    const response = await api.post('/login', credentials);
    return response.data;
  },

  logout: () => localStorage.removeItem('user'),

  getCurrentUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  }
};