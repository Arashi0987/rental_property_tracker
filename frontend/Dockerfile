# Stage 1: build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./
COPY frontend/tsconfig.json ./
COPY frontend/next.config.js ./

# Install dependencies
RUN npm install

# Copy all frontend source
COPY frontend/ ./

# Build the Next.js app
RUN npm run build

# Stage 2: production image
FROM node:20-alpine AS runner

WORKDIR /app

# Copy build output and necessary files
COPY --from=builder /app/ ./

# Install only production dependencies
RUN npm prune --production

# Expose the port Next.js runs on (default 3000)
EXPOSE 3000

# Start the server
CMD ["npm", "start"]
