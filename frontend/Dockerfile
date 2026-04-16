# Stage 1: Build the React Application
FROM node:18-alpine AS build

WORKDIR /app

# Copy package configurations
COPY package.json package-lock.json* ./

# Install dependencies (ignoring scripts)
RUN npm ci

# Copy the rest of the application
COPY . .

# Build the Vite project targeting the 'dist' folder
RUN npm run build

# Stage 2: Serve the application using Nginx
FROM nginx:alpine

# Remove default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d

# Copy the built React app from the build stage map it to Nginx's hosting directory
COPY --from=build /app/dist /usr/share/nginx/html

# Expose Port 80 for web traffic
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
