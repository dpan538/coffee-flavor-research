import { index, route, type RouteConfig } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("atlas", "routes/atlas.tsx"),
  route("methodology", "routes/methodology.tsx"),
  route("flavor/:slug", "routes/flavor.tsx"),
] satisfies RouteConfig;
