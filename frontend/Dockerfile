# ------------ 1. Build Stage ------------ 
FROM node:20 AS build
WORKDIR /app 
COPY package*.json ./ 
RUN npm install 

COPY . . 
RUN npm run build

# ------------ 2. Nginx Production Stage ------------ 
FROM nginx:1.25-alpine

# 刪除 default.conf（避免衝突） 
RUN rm /etc/nginx/conf.d/default.conf 
# 複製前端 build 出來的檔案 
COPY --from=build /app/dist /usr/share/nginx/html 
# 複製自訂的 nginx.conf 
COPY nginx.conf /etc/nginx/conf.d/default.conf 
EXPOSE 80 
CMD ["nginx", "-g", "daemon off;"]