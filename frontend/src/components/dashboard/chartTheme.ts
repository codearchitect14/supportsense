import { chartChrome } from "../../lib/chartPalette";

export const tooltipContentStyle = {
  background: "#ffffff",
  border: `1px solid ${chartChrome.gridline}`,
  borderRadius: 8,
  fontSize: 12,
  boxShadow: "0 4px 12px rgba(11,11,11,0.08)",
};

export const tooltipLabelStyle = { color: chartChrome.secondaryInk, fontWeight: 600 };
export const axisTickStyle = { fill: chartChrome.mutedInk, fontSize: 11 };
export const legendStyle = { fontSize: 12, color: chartChrome.secondaryInk };
