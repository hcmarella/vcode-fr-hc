# Multi-stage: `dev` is the Vite dev server used by docker-compose.yml
# (build target: dev). `prod` builds the static bundle and serves it via
# nginx, which also reverse-proxies /api to the backend Service -- Vite's
# dev-only proxy (vite.config.ts) has no equivalent once there's no dev
# server running, so nginx.conf.template replaces that role in prod.

FROM node:20-slim AS base
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

# ---- dev: used by docker-compose.yml ----
FROM base AS dev
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ---- build: compiles the static bundle for the prod stage ----
FROM base AS build
RUN npm run build

# ---- prod: used by terraform/ECR build + k8s deployments ----
FROM nginx:1.27-alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx.conf.template /etc/nginx/templates/default.conf.template
ENV BACKEND_UPSTREAM=backend:8000
EXPOSE 80
