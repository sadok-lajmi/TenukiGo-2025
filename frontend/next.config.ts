import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  images: {
    domains: [process.env.NEXT_PUBLIC_API_HOST ?? "", 'localhost'],
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/storage/**',
      },
      {
        protocol: 'http',
        hostname: 'backend',
        port: '8000',
        pathname: '/storage/**',
      },
    ],
  },
  // Configuration Webpack pour forcer le Hot Reload sous Docker
  webpack: (config, context) => {
    if (context.dev) {
        config.watchOptions = {
            poll: 1000,   // Vérifie les changements toutes les secondes
            aggregateTimeout: 300, // Attend 300ms après un changement avant de rebuild
        }
    }
    return config;
  },
};

export default nextConfig;
