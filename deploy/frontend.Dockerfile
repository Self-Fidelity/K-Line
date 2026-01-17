# Build Stage
FROM node:18-alpine as build-stage

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY frontend/ .

# Build arguments
ARG VITE_API_BASE_URL
ARG VITE_BASE_PATH
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_BASE_PATH=$VITE_BASE_PATH

# Build
RUN npm run build

# Production Stage
FROM nginx:alpine as production-stage

# Copy build artifacts
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy Nginx config
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
