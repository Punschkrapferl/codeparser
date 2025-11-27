FROM node:22-alpine AS build

WORKDIR /usr/src/app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy the rest of the Angular app
COPY . .

# Build Angular for production
RUN npm run build -- --configuration production

# Serve with Nginx
FROM nginx:stable-alpine

# Simple SPA config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built app
COPY --from=build /usr/src/app/dist/parserUI/browser /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
