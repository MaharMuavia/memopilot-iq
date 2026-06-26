// Lightweight line-icon set (feather/lucide-style, stroke = currentColor).
// Replaces emoji throughout the UI for a consistent, professional look.
import type { ReactNode, SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { size?: number };

function Svg({ size = 18, children, ...props }: IconProps & { children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export const IconChat = (p: IconProps) => (
  <Svg {...p}><path d="M21 11.5a8.38 8.38 0 0 1-8.5 8.5 8.5 8.5 0 0 1-3.9-.9L3 21l1.9-5.6A8.38 8.38 0 0 1 4 11.5 8.5 8.5 0 0 1 12.5 3 8.38 8.38 0 0 1 21 11.5z" /></Svg>
);
export const IconTrace = (p: IconProps) => (
  <Svg {...p}><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" /><circle cx="12" cy="12" r="3" /></Svg>
);
export const IconGraph = (p: IconProps) => (
  <Svg {...p}><circle cx="6" cy="6" r="2.5" /><circle cx="18" cy="7" r="2.5" /><circle cx="9" cy="18" r="2.5" /><circle cx="18" cy="17" r="2.5" /><path d="M8 7.5 15.5 7M8 16l8.2-7M11 17.5h4.5" /></Svg>
);
export const IconTimeline = (p: IconProps) => (
  <Svg {...p}><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></Svg>
);
export const IconAnalytics = (p: IconProps) => (
  <Svg {...p}><path d="M3 3v18h18" /><path d="M7 14l3-4 3 2 4-6" /></Svg>
);
export const IconEval = (p: IconProps) => (
  <Svg {...p}><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /></Svg>
);
export const IconControls = (p: IconProps) => (
  <Svg {...p}><path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6" /></Svg>
);
export const IconSettings = (p: IconProps) => (
  <Svg {...p}><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></Svg>
);

export const IconPlay = (p: IconProps) => (
  <Svg {...p}><path d="M6 4l14 8-14 8V4z" /></Svg>
);
export const IconSparkle = (p: IconProps) => (
  <Svg {...p}><path d="M12 3l1.8 4.7L18.5 9l-4.7 1.3L12 15l-1.8-4.7L5.5 9l4.7-1.3L12 3z" /><path d="M19 14l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7L19 14z" /></Svg>
);
export const IconPin = (p: IconProps) => (
  <Svg {...p}><path d="M12 17v5" /><path d="M9 10.5V4h6v6.5l2.5 3.5h-11L9 10.5z" /></Svg>
);
export const IconArchive = (p: IconProps) => (
  <Svg {...p}><rect x="3" y="4" width="18" height="4" rx="1" /><path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8M10 12h4" /></Svg>
);
export const IconTrash = (p: IconProps) => (
  <Svg {...p}><path d="M3 6h18M8 6V4h8v2M19 6l-1 14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1L5 6M10 11v6M14 11v6" /></Svg>
);
export const IconDownload = (p: IconProps) => (
  <Svg {...p}><path d="M12 3v12M7 10l5 5 5-5M5 21h14" /></Svg>
);
export const IconSend = (p: IconProps) => (
  <Svg {...p}><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" /></Svg>
);
export const IconHome = (p: IconProps) => (
  <Svg {...p}><path d="M15 18l-6-6 6-6" /></Svg>
);
export const IconGithub = (p: IconProps) => (
  <Svg {...p}><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12 12 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21" /></Svg>
);
export const IconCheck = (p: IconProps) => (
  <Svg {...p}><path d="M20 6 9 17l-5-5" /></Svg>
);
export const IconShield = (p: IconProps) => (
  <Svg {...p}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="M9 12l2 2 4-4" /></Svg>
);

// Landing / feature icons
export const IconLayers = (p: IconProps) => (
  <Svg {...p}><path d="M12 2 2 7l10 5 10-5-10-5zM2 12l10 5 10-5M2 17l10 5 10-5" /></Svg>
);
export const IconLink = (p: IconProps) => (
  <Svg {...p}><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1.5 1.5M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1.5-1.5" /></Svg>
);
export const IconHourglass = (p: IconProps) => (
  <Svg {...p}><path d="M6 2h12M6 22h12M6 2c0 5 6 6 6 10 0-4 6-5 6-10M6 22c0-5 6-6 6-10 0 4 6 5 6 10" /></Svg>
);
export const IconTarget = (p: IconProps) => (
  <Svg {...p}><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1.5" /></Svg>
);
export const IconGauge = (p: IconProps) => (
  <Svg {...p}><path d="M12 14a6 6 0 1 0-6-6" opacity="0" /><path d="M4 18a8 8 0 1 1 16 0" /><path d="M12 14l4-4" /><circle cx="12" cy="14" r="1.4" /></Svg>
);
export const IconPuzzle = (p: IconProps) => (
  <Svg {...p}><path d="M9 5a2 2 0 1 1 4 0c0 .5.5 1 1 1h2a1 1 0 0 1 1 1v2c0 .5.5 1 1 1a2 2 0 1 1 0 4c-.5 0-1 .5-1 1v2a1 1 0 0 1-1 1h-2c-.5 0-1 .5-1 1a2 2 0 1 1-4 0c0-.5-.5-1-1-1H5a1 1 0 0 1-1-1v-2c0-.5-.5-1-1-1a2 2 0 1 1 0-4c.5 0 1-.5 1-1V7a1 1 0 0 1 1-1h2c.5 0 1-.5 1-1z" /></Svg>
);
export const IconRepeat = (p: IconProps) => (
  <Svg {...p}><path d="M17 2l4 4-4 4" /><path d="M3 11V9a4 4 0 0 1 4-4h14M7 22l-4-4 4-4" /><path d="M21 13v2a4 4 0 0 1-4 4H3" /></Svg>
);
export const IconTrendingDown = (p: IconProps) => (
  <Svg {...p}><path d="M22 17l-8.5-8.5-5 5L2 7" /><path d="M16 17h6v-6" /></Svg>
);
export const IconUser = (p: IconProps) => (
  <Svg {...p}><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></Svg>
);
export const IconMonitor = (p: IconProps) => (
  <Svg {...p}><rect x="3" y="4" width="18" height="12" rx="2" /><path d="M8 20h8M12 16v4" /></Svg>
);
export const IconServer = (p: IconProps) => (
  <Svg {...p}><rect x="3" y="4" width="18" height="6" rx="2" /><rect x="3" y="14" width="18" height="6" rx="2" /><path d="M7 7h.01M7 17h.01" /></Svg>
);
export const IconCpu = (p: IconProps) => (
  <Svg {...p}><rect x="6" y="6" width="12" height="12" rx="2" /><path d="M9 9h6v6H9zM9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3" /></Svg>
);
export const IconCloud = (p: IconProps) => (
  <Svg {...p}><path d="M17.5 19a4.5 4.5 0 0 0 .5-9 6 6 0 0 0-11.6-1.5A4 4 0 0 0 7 19h10.5z" /></Svg>
);
export const IconDatabase = (p: IconProps) => (
  <Svg {...p}><ellipse cx="12" cy="5" rx="8" ry="3" /><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" /></Svg>
);
