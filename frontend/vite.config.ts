import fs from "node:fs";
import path from "node:path";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

function serveAppStaticFonts(): Plugin {
  const fontsRoot = path.resolve(__dirname, "../app/static/fonts");
  return {
    name: "serve-app-static-fonts",
    configureServer(server) {
      server.middlewares.use("/static/fonts", (req, res, next) => {
        const rel = (req.url || "").split("?")[0];
        const filePath = path.join(fontsRoot, rel);
        if (!filePath.startsWith(fontsRoot) || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
          next();
          return;
        }
        const ext = path.extname(filePath);
        const types: Record<string, string> = {
          ".css": "text/css; charset=utf-8",
          ".woff2": "font/woff2",
        };
        res.setHeader("Content-Type", types[ext] || "application/octet-stream");
        fs.createReadStream(filePath).pipe(res);
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), serveAppStaticFonts()],
  base: "/static/helpdesk/",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  build: {
    outDir: path.resolve(__dirname, "../app/static/helpdesk"),
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: "assets/[name]-[hash].js",
        chunkFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash][extname]",
      },
    },
  },
});
