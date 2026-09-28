import axios from 'axios';

export const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const api = axios.create({
    baseURL: `${API_BASE}/api`,
    withCredentials: true,
});

export default api;
