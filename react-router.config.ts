import type { Config } from "@react-router/dev/config";
import { descriptors } from "./packages/flavor-data/src";

const descriptorPaths = descriptors.map(
  (descriptor) => `/flavor/${descriptor.slug}`,
);

export default {
  ssr: false,
  prerender: ["/", "/atlas", "/methodology", ...descriptorPaths],
} satisfies Config;
