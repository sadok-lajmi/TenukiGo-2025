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
  // Webpack configuration to force Hot Reload under Docker
  webpack: (config, context) => {
    if (context.dev) {
        config.watchOptions = {
            poll: 1000,   // Check for changes every second
            aggregateTimeout: 300, // Wait 300ms after a change before rebuilding
        }
    }
    return config;
  },
};

export default nextConfig;
