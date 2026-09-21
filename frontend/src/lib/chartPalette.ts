// Validated categorical/sequential/status palette (see the dataviz skill's
// references/palette.md). Order is the CVD-safety mechanism, never reorder
// or cycle past what a chart actually needs.
export const categorical = [
  "#2a78d6", // 1 blue
  "#eb6834", // 2 orange
  "#1baf7a", // 3 aqua
  "#eda100", // 4 yellow
  "#e87ba4", // 5 magenta
  "#008300", // 6 green
  "#4a3aa7", // 7 violet
  "#e34948", // 8 red
];

export const sequentialBlue = {
  100: "#cde2fb",
  150: "#b7d3f6",
  200: "#9ec5f4",
  250: "#86b6ef",
  300: "#6da7ec",
  350: "#5598e7",
  400: "#3987e5",
  450: "#2a78d6",
  500: "#256abf",
  550: "#1c5cab",
  600: "#184f95",
  650: "#104281",
  700: "#0d366b",
};

// Discrete ordered ramp (e.g. a 1-5 star rating), not continuous magnitude:
// the lightest step must still clear 2:1 contrast, so start at 250, not 100.
export const ordinalBlueSteps = [
  sequentialBlue[250],
  sequentialBlue[350],
  sequentialBlue[450],
  sequentialBlue[550],
  sequentialBlue[650],
];

export const status = {
  good: "#0ca30c",
  warning: "#fab219",
  serious: "#ec835a",
  critical: "#d03b3b",
};

export const chartChrome = {
  gridline: "#e1e0d9",
  axis: "#c3c2b7",
  mutedInk: "#898781",
  secondaryInk: "#52514e",
  primaryInk: "#0b0b0b",
};
