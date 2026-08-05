FROM node:22-alpine
WORKDIR /app
COPY package.json ./
RUN corepack enable && pnpm install --frozen-lockfile=false
COPY . .
EXPOSE 5173
CMD ["pnpm", "dev", "--host", "0.0.0.0"]

