"use client";

import Image from "next/image";

interface HeatmapViewerProps {
  original: string | null;
  heatmap: string | null;
  alpha: number;
}

export default function HeatmapViewer({
  original,
  heatmap,
  alpha,
}: HeatmapViewerProps) {
  return (
    <div className="relative w-full aspect-square bg-slate-900 rounded-xl overflow-hidden border border-slate-700">
      {original ? (
        <Image
          src={original}
          alt="Chest X-ray"
          fill
          className="object-contain"
          priority
        />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center text-slate-500">
          No image selected
        </div>
      )}
      {heatmap && (
        <Image
          src={heatmap}
          alt="Grad-CAM heatmap"
          fill
          className="object-contain transition-opacity duration-100"
          style={{ opacity: alpha / 100, mixBlendMode: "screen" }}
          priority
        />
      )}
    </div>
  );
}
