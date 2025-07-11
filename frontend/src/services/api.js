import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // Tăng timeout cho template matching
});

export const imageService = {
  // ✅ GIỮ NGUYÊN FUNCTION CŨ
  compareImages: async (image1, image2) => {
    const formData = new FormData();
    formData.append('image1', image1);
    formData.append('image2', image2);

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

  // ✅ THÊM FUNCTION MỚI CHO TEMPLATE MATCHING
  compareWithUrl: async (templateImage, url) => {
    const formData = new FormData();
    formData.append('image1', templateImage);  // Template
    formData.append('compare_url', url);       // URL instead of image2

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

  getImageUrl: (filename, type = 'uploads') => {
    return `${API_BASE_URL}/${type}/${filename}`;
  },
};