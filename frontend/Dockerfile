# frontend/Dockerfile
# The development variant contains npm and a shell for the build while retaining
# Chainguard's reduced package and CVE surface.
FROM cgr.dev/chainguard/node:latest-dev AS build

WORKDIR /app

COPY --chown=node:node package.json package-lock.json ./
RUN npm ci

# Accept the backend URL as a build-time arg and expose it to Vite.
# Vite only bakes in variables prefixed with VITE_ at build time.
ARG VITE_BACKEND_URL=""
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}

COPY --chown=node:node . .
RUN npm run build

# Minimal, non-root runtime image. It listens on 8080 because an unprivileged
# process cannot bind to port 80.
FROM cgr.dev/chainguard/nginx:latest AS runtime

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["nginx", "-t"]

# The image entrypoint is already /usr/sbin/nginx, so CMD contains arguments
# only. Supplying "nginx" again would result in an invalid command.
CMD ["-g", "daemon off;"]
