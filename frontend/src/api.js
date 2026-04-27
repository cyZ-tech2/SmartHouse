import axios from "axios";

export const API_URL = "http://127.0.0.1:8000/api";

const API = axios.create({ baseURL: API_URL });

API.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const saveAuth = (data) => {
  localStorage.setItem("access", data.access);
  localStorage.setItem("refresh", data.refresh);
  if (data.user) localStorage.setItem("user", JSON.stringify(data.user));
};

export const clearAuth = () => {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  localStorage.removeItem("user");
};

export const getUser = () => {
  const u = localStorage.getItem("user");
  return u ? JSON.parse(u) : null;
};

export const refreshUser = async () => {
  const { data } = await API.get("/profile/");
  localStorage.setItem("user", JSON.stringify(data));
  return data;
};

export const isLoggedIn = () => !!localStorage.getItem("access");

export const isChild = () => {
  const u = getUser();
  return u && u.role === "enfant";
};

export const isAdvanced = () => {
  const u = getUser();
  // Un enfant n'a JAMAIS accès au module Gestion
  if (!u || u.role === "enfant") return false;
  return u.level === "avance" || u.level === "expert";
};

export const isAdmin = () => {
  const u = getUser();
  return u && (u.is_staff === true || u.username === "admin");
};

export default API;
