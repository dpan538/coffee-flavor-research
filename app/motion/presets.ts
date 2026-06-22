export const motionDurations = {
  fast: 180,
  medium: 420,
  slow: 900,
};

export const motionEases = {
  editorial: "outExpo",
  soft: "inOutSine",
  snap: "outCubic",
};

export const motionFamilies = [
  "bloom",
  "cluster",
  "drip",
  "fracture",
  "vapor",
  "bubble",
  "orbit",
  "dissolve",
] as const;

export type MotionFamily = (typeof motionFamilies)[number];
