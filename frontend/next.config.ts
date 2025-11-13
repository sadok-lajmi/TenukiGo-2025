import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  images: {
    domains: [process.env.NEXT_PUBLIC_API_HOST ?? "", 'localhost'],
  },
};

export default nextConfig;
