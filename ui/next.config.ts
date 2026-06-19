import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow the Render backend domain in production
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
        ],
      },
    ];
  },
};

export default nextConfig;
