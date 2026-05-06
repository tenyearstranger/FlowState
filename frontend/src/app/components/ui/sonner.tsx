import type { CSSProperties } from "react";
import { Toaster as Sonner, type ToasterProps } from "sonner";

const toasterStyle = {
  "--normal-bg": "rgba(18, 18, 24, 0.96)",
  "--normal-text": "rgba(255,255,255,0.92)",
  "--normal-border": "rgba(255,255,255,0.1)",
  "--success-bg": "rgba(11, 31, 18, 0.96)",
  "--success-text": "#7DFFAE",
  "--success-border": "rgba(52,199,89,0.24)",
  "--error-bg": "rgba(41, 15, 15, 0.96)",
  "--error-text": "#FF8A80",
  "--error-border": "rgba(255,69,58,0.24)",
} as CSSProperties;

export function Toaster(props: ToasterProps) {
  return (
    <Sonner
      theme="dark"
      position="top-center"
      richColors
      closeButton
      toastOptions={{
        style: {
          borderRadius: "14px",
          backdropFilter: "blur(18px)",
          boxShadow: "0 18px 50px rgba(0,0,0,0.28)",
        },
      }}
      style={toasterStyle}
      {...props}
    />
  );
}
