import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000,
});

export const imageService = {
  compareImages: async (image1, image2, userId, projectId = null) => {
    const formData = new FormData();
    formData.append('image1', image1);
    formData.append('image2', image2);
    formData.append('user_id', userId);
    if (projectId) formData.append('project_id', projectId);

    const response = await api.post('/upload', formData);
    return response.data;
  },

  compareWithUrl: async (templateImage, url, userId, projectId = null) => {
    const formData = new FormData();
    formData.append('image1', templateImage);
    formData.append('compare_url', url);
    formData.append('user_id', userId);
    if (projectId) formData.append('project_id', projectId);

    const response = await api.post('/upload', formData);
    return response.data;
  },

  getUserComparisons: async (userId) => {
    const response = await api.get(`/users/${userId}/comparisons`);
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