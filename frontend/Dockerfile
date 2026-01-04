# 1. Use a lightweight official Node.js image (Alpine)
FROM node:22-alpine

# [OPTIMIZATION] Install libc6-compat
# Required for Next.js/SWC on Alpine (prevents silent build bugs or crashes)
RUN apk add --no-cache libc6-compat

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy dependency definition files
# Done before copying the rest of the code to leverage Docker cache
COPY package.json package-lock.json* ./

# 4. Install dependencies
RUN npm install

# 5. Copy the rest of the frontend source code
COPY . .

# 6. Expose the port on which Next.js runs by default
EXPOSE 3000

# 7. Startup command for development
# Launches Next.js server in dev mode with hot-reloading
CMD ["npm", "run", "dev"]
