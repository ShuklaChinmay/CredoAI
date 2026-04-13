// import axios from "axios";

// const API = "https://credoai-backend.onrender.com";

// const authService = {
//   login: (email, password) =>
//     axios.post(`${API}/auth/login`, { email, password }),

//   register: (data) =>
//     axios.post(`${API}/auth/register`, data),

//   verifyOtp: (email, otp) =>
//     axios.post(`${API}/auth/verify-otp`, { email, otp }),

//   forgotPassword: (email) =>
//     axios.post(`${API}/auth/forgot-password`, { email }),

//   resetPassword: (email, otp, new_password) =>
//     axios.post(`${API}/auth/reset-password`, {
//       email,
//       otp,
//       new_password,
//     }),
// };

// export default authService;



import api from "./api";

const authService = {
  login: (email, password) =>
    api.post("/auth/login", { email, password }),

  register: (data) =>
    api.post("/auth/register", data),

  verifyOtp: (email, otp) =>
    api.post("/auth/verify-otp", { email, otp }),

  forgotPassword: (email) =>
    api.post("/auth/forgot-password", { email }),

  resetPassword: (email, otp, new_password) =>
    api.post("/auth/reset-password", {
      email,
      otp,
      new_password,
    }),

  resendOtp: (email) =>
    api.post("/auth/resend-otp", { email }),
};

export default authService;