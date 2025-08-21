import axios from "axios";

const instance = axios.create({
  baseURL: "http://localhost:8000",
});

// 設定 Authorization header
export const setAuthToken = (token) => {
  if (token) {
    instance.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete instance.defaults.headers.common["Authorization"];
  }
};

// 攔截器自動刷新 token
instance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response &&
      error.response.status === 401 &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;
      const refresh_token = localStorage.getItem("refresh_token");
      if (refresh_token) {
        try {
          const res = await axios.post(
            "http://localhost:8000/auth/refresh-token",
            { token: refresh_token }
          );
          const new_access_token = res.data.access_token;
          localStorage.setItem("access_token", new_access_token);
          setAuthToken(new_access_token);
          originalRequest.headers["Authorization"] = `Bearer ${new_access_token}`;
          return axios(originalRequest);
        } catch (err) {
          console.log("刷新 token 失敗", err);
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          setAuthToken(null);
          window.location.href = "/login";
        }
      } else {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default instance;
