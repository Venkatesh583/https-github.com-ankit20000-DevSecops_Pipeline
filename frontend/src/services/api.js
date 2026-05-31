import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

// API Base URLs - Configure based on environment
const API_BASE_URLS = {
  USER_SERVICE: process.env.REACT_APP_USER_SERVICE_URL || 'http://localhost:5001',
  APPOINTMENT_SERVICE: process.env.REACT_APP_APPOINTMENT_SERVICE_URL || 'http://localhost:5002',
  REPORT_SERVICE: process.env.REACT_APP_REPORT_SERVICE_URL || 'http://localhost:5003'
};

// Create axios instances for each service
const createAxiosInstance = (baseURL) => {
  const instance = axios.create({
    baseURL,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json'
    }
  });

  // Add request interceptor to attach JWT token
  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Add response interceptor to handle errors
  instance.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );

  return instance;
};

const userService = createAxiosInstance(API_BASE_URLS.USER_SERVICE);
const appointmentService = createAxiosInstance(API_BASE_URLS.APPOINTMENT_SERVICE);
const reportService = createAxiosInstance(API_BASE_URLS.REPORT_SERVICE);

// ============== USER SERVICE ENDPOINTS ==============

export const userAPI = {
  // Register new user
  register: (userData) => 
    userService.post('/register', userData),

  // Login user
  login: (email, password) =>
    userService.post('/login', { email, password }),

  // Get current user profile
  getProfile: () =>
    userService.get('/users/profile'),

  // Update user profile
  updateProfile: (profileData) =>
    userService.put('/users/profile', profileData),

  // Get user by ID (admin/doctor)
  getUserById: (userId) =>
    userService.get(`/users/${userId}`),

  // List all doctors
  getDoctors: () =>
    userService.get('/doctors'),

  // Get doctor by ID
  getDoctorById: (doctorId) =>
    userService.get(`/doctors/${doctorId}`),

  // Health check
  healthCheck: () =>
    userService.get('/health')
};

// ============== APPOINTMENT SERVICE ENDPOINTS ==============

export const appointmentAPI = {
  // Get list of doctors
  listDoctors: () =>
    appointmentService.get('/doctors'),

  // Book appointment
  bookAppointment: (appointmentData) =>
    appointmentService.post('/appointments', appointmentData),

  // Get appointment history
  getHistory: () =>
    appointmentService.get('/appointments/history'),

  // Get specific appointment
  getAppointment: (appointmentId) =>
    appointmentService.get(`/appointments/${appointmentId}`),

  // Get appointments for a patient
  getPatientAppointments: (patientId) =>
    appointmentService.get(`/appointments/patient/${patientId}`),

  // Cancel appointment
  cancelAppointment: (appointmentId) =>
    appointmentService.post(`/appointments/${appointmentId}/cancel`),

  // Confirm appointment (doctor)
  confirmAppointment: (appointmentId, notes = '') =>
    appointmentService.post(`/appointments/${appointmentId}/confirm`, { notes }),

  // Delete appointment
  deleteAppointment: (appointmentId) =>
    appointmentService.delete(`/appointments/${appointmentId}`),

  // Health check
  healthCheck: () =>
    appointmentService.get('/health')
};

// ============== REPORT SERVICE ENDPOINTS ==============

export const reportAPI = {
  // Upload medical report
  uploadReport: (formData) =>
    reportService.post('/reports/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  // Get user's reports
  getReports: () =>
    reportService.get('/reports/list'),

  // Get reports for patient (doctor)
  getPatientReports: (patientId) =>
    reportService.get(`/reports/patient/${patientId}`),

  // Get specific report
  getReport: (reportId) =>
    reportService.get(`/reports/${reportId}`),

  // Download report (get presigned URL)
  downloadReport: (reportId) =>
    reportService.get(`/reports/${reportId}/download`),

  // Delete report
  deleteReport: (reportId) =>
    reportService.delete(`/reports/${reportId}/delete`),

  // Health check
  healthCheck: () =>
    reportService.get('/health')
};

// ============== AUTH UTILITIES ==============

export const authUtils = {
  // Check if user is logged in
  isLoggedIn: () => !!localStorage.getItem('access_token'),

  // Get current user from localStorage
  getCurrentUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  // Get current token
  getToken: () => localStorage.getItem('access_token'),

  // Check if token is expired
  isTokenExpired: () => {
    const token = localStorage.getItem('access_token');
    if (!token) return true;
    try {
      const decoded = jwtDecode(token);
      return decoded.exp * 1000 < Date.now();
    } catch (e) {
      return true;
    }
  },

  // Save login data
  saveLoginData: (token, user) => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('user', JSON.stringify(user));
  },

  // Clear login data
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },

  // Check user role
  hasRole: (role) => {
    const user = authUtils.getCurrentUser();
    return user && user.role === role;
  }
};

// ============== HEALTH CHECK ==============

export const healthCheck = async () => {
  try {
    const results = await Promise.all([
      userAPI.healthCheck(),
      appointmentAPI.healthCheck(),
      reportAPI.healthCheck()
    ]);
    return {
      success: true,
      services: {
        userService: results[0].status === 200,
        appointmentService: results[1].status === 200,
        reportService: results[2].status === 200
      }
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
};

export default {
  userAPI,
  appointmentAPI,
  reportAPI,
  authUtils,
  healthCheck
};
