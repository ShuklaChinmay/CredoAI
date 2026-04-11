// import axios from "axios";

import api from "./api"; 


import api from "./api"; // 👈 use common axios instance

const authService = {
  login: (email, password) =>
    api.post(`/auth/login`, { email, password }),

  register: (data) =>
    api.post(`/auth/register`, data),

  verifyOtp: (email, otp) =>
    api.post(`/auth/verify-otp`, { email, otp }),

  forgotPassword: (email) =>
    api.post(`/auth/forgot-password`, { email }),

  resetPassword: (email, otp, new_password) =>
    api.post(`/auth/reset-password`, {
      email,
      otp,
      new_password,
    }),
};

export default authService;