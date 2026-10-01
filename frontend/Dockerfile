FROM node:22.22.0-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.28.0-alpine
ENV FRONTEND_PORT=8080 API_UPSTREAM=http://api:8000
ENV IMAGE_MAX_BYTES=10485760 AUDIO_MAX_BYTES=104857600
ENV UPLOAD_MAX_BODY_SIZE=128m API_READ_TIMEOUT=600s
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
