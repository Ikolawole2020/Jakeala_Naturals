/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "jakealanaturals.pythonanywhere.com" },
      { protocol: "http", hostname: "localhost" },
    ],
  },
};

module.exports = nextConfig;
