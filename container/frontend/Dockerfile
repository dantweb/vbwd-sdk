# Build stage - User app
FROM node:20-alpine AS build-user

WORKDIR /app/user
COPY user/vue/package*.json ./
RUN npm ci
COPY user/vue/ ./
RUN npm run build

# Build stage - Admin app
FROM node:20-alpine AS build-admin

WORKDIR /app/admin
COPY admin/vue/package*.json ./
RUN npm ci
COPY admin/vue/ ./
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=build-user /app/user/dist /usr/share/nginx/html/user
COPY --from=build-admin /app/admin/dist /usr/share/nginx/html/admin

# Copy nginx config
COPY ../container/frontend/nginx.conf /etc/nginx/nginx.conf

# Create log directory
RUN mkdir -p /var/log/nginx

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
