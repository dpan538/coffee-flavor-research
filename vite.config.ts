import { reactRouter } from "@react-router/dev/vite";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [
    {
      name: "coffee-atlas-clean-preview-urls",
      configurePreviewServer(server) {
        server.middlewares.use((request, _response, next) => {
          if (!request.url) {
            next();
            return;
          }

          const [pathname, search = ""] = request.url.split("?");
          const shouldRedirectToDirectory =
            pathname === "/atlas" ||
            pathname === "/methodology" ||
            /^\/flavor\/[^/]+$/.test(pathname ?? "");

          if (shouldRedirectToDirectory) {
            request.url = `${pathname}/`;
            if (search) {
              request.url += `?${search}`;
            }
          }

          next();
        });
      },
    },
    reactRouter(),
  ],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./app", import.meta.url)),
      "flavor-data": fileURLToPath(
        new URL("./packages/flavor-data/src/index.ts", import.meta.url),
      ),
    },
  },
});
