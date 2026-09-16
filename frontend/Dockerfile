# Stage 1: build de la app SvelteKit (adapter-static genera ./build)
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# URL del servicio de métricas consumido por /dashboard.
# Se hornea en el bundle estático (adapter-static) — configurable, nunca hardcodeada en el código.
ARG PUBLIC_METRICS_URL=http://localhost:8000/api/internal/notes-status/
ENV PUBLIC_METRICS_URL=$PUBLIC_METRICS_URL

RUN npm run build

# Stage 2: servir los estáticos con Nginx
FROM nginx:1.27-alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
