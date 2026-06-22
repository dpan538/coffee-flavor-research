export type DescriptorAssetCandidate = {
  slug: string;
  library: string;
  originalIconName: string;
  author: string;
  originalUrl: string;
  localPath: string;
  license: string;
  attributionRequired: boolean;
  modifications: string;
  motionFamily:
    | "bloom"
    | "cluster"
    | "drip"
    | "fracture"
    | "vapor"
    | "bubble"
    | "orbit"
    | "dissolve";
  evaluation: {
    recognizability: "high" | "medium" | "low";
    styleFit: "high" | "medium" | "low";
    animationFit: "high" | "medium" | "low";
    monochromeFit: "high" | "medium" | "low";
  };
};

export const descriptorAssets: DescriptorAssetCandidate[] = [
  {
    slug: "jasmine",
    library: "Game-icons.net",
    originalIconName: "Jasmine",
    author: "Delapouite",
    originalUrl: "https://game-icons.net/1x1/delapouite/jasmine.html",
    localPath: "/vendor/game-icons/jasmine.svg",
    license: "CC BY 3.0",
    attributionRequired: true,
    modifications:
      "Candidate SVG is framed inside the Atlas specimen system; no path edits in this spike.",
    motionFamily: "bloom",
    evaluation: {
      recognizability: "high",
      styleFit: "medium",
      animationFit: "high",
      monochromeFit: "high",
    },
  },
  {
    slug: "lemon",
    library: "Game-icons.net",
    originalIconName: "Lemon",
    author: "Delapouite",
    originalUrl: "https://game-icons.net/1x1/delapouite/lemon.html",
    localPath: "/vendor/game-icons/lemon.svg",
    license: "CC BY 3.0",
    attributionRequired: true,
    modifications:
      "Candidate SVG is framed inside the Atlas specimen system; no path edits in this spike.",
    motionFamily: "orbit",
    evaluation: {
      recognizability: "high",
      styleFit: "medium",
      animationFit: "medium",
      monochromeFit: "high",
    },
  },
  {
    slug: "red-berries",
    library: "Game-icons.net",
    originalIconName: "Berries bowl",
    author: "Delapouite",
    originalUrl: "https://game-icons.net/1x1/delapouite/berries-bowl.html",
    localPath: "/vendor/game-icons/berries-bowl.svg",
    license: "CC BY 3.0",
    attributionRequired: true,
    modifications:
      "Candidate SVG is framed inside the Atlas specimen system; no path edits in this spike.",
    motionFamily: "cluster",
    evaluation: {
      recognizability: "medium",
      styleFit: "medium",
      animationFit: "high",
      monochromeFit: "high",
    },
  },
  {
    slug: "dark-chocolate",
    library: "Game-icons.net",
    originalIconName: "Chocolate bar",
    author: "Rihlsul",
    originalUrl: "https://game-icons.net/1x1/rihlsul/chocolate-bar.html",
    localPath: "/vendor/game-icons/chocolate-bar.svg",
    license: "CC BY 3.0",
    attributionRequired: true,
    modifications:
      "Candidate SVG is framed inside the Atlas specimen system; no path edits in this spike.",
    motionFamily: "fracture",
    evaluation: {
      recognizability: "high",
      styleFit: "medium",
      animationFit: "high",
      monochromeFit: "high",
    },
  },
  {
    slug: "cinnamon",
    library: "Game-icons.net",
    originalIconName: "Hot spices",
    author: "Lorc",
    originalUrl: "https://game-icons.net/1x1/lorc/hot-spices.html",
    localPath: "/vendor/game-icons/hot-spices.svg",
    license: "CC BY 3.0",
    attributionRequired: true,
    modifications:
      "Chosen as a cinnamon-adjacent candidate because a direct cinnamon stick icon was not selected for the first spike; no path edits.",
    motionFamily: "vapor",
    evaluation: {
      recognizability: "medium",
      styleFit: "medium",
      animationFit: "high",
      monochromeFit: "high",
    },
  },
  {
    slug: "cheese",
    library: "Game-icons.net",
    originalIconName: "Cheese wedge",
    author: "Lorc",
    originalUrl: "https://game-icons.net/1x1/lorc/cheese-wedge.html",
    localPath: "/vendor/game-icons/cheese-wedge.svg",
    license: "CC BY 3.0",
    attributionRequired: true,
    modifications:
      "Candidate SVG is framed inside the Atlas specimen system; no path edits in this spike.",
    motionFamily: "bubble",
    evaluation: {
      recognizability: "high",
      styleFit: "medium",
      animationFit: "medium",
      monochromeFit: "high",
    },
  },
];

export const descriptorAssetBySlug = Object.fromEntries(
  descriptorAssets.map((asset) => [asset.slug, asset]),
) as Record<string, DescriptorAssetCandidate | undefined>;
