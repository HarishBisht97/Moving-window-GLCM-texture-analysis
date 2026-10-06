import { Download, Maximize2, Minus, Plus, RotateCcw, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type PointerEvent, type ReactNode, type WheelEvent } from "react";
import { downloadResult } from "../../api/analysis";
import type { ColorLegend as ColorLegendData } from "../../types/analysis";
import { IconButton } from "../common/Button";
import { ColorLegend } from "./ColorLegend";

interface ImageViewerProps {
  src: string;
  title: string;
  subtitle?: string;
  /** Backend file URL to download (defaults to `src`). */
  downloadSrc?: string | null;
  legend?: ColorLegendData;
  /** width / height of the image, keeps tiles aligned before the image loads. */
  aspectRatio?: number;
  /** Nearest-neighbour rendering (useful for label maps). */
  pixelated?: boolean;
  compact?: boolean;
  /** Show the legend under the tile (it is always shown in fullscreen). */
  inlineLegend?: boolean;
  footer?: ReactNode;
}

export function ImageViewer({
  src,
  title,
  subtitle,
  downloadSrc,
  legend,
  aspectRatio,
  pixelated = false,
  compact = false,
  inlineLegend = true,
  footer,
}: ImageViewerProps) {
  const [open, setOpen] = useState(false);
  const download = downloadSrc === undefined ? src : downloadSrc;
  const showLegend = legend !== undefined && inlineLegend;

  return (
    <figure className="flex min-w-0 flex-col self-start rounded-md border border-slate-200 bg-white">
      <figcaption className={`flex items-center justify-between gap-2 border-b border-slate-100 ${compact ? "px-2 py-1" : "px-3 py-1.5"}`}>
        <div className="min-w-0">
          <p className={`truncate font-medium text-slate-800 ${compact ? "text-[11px]" : "text-xs"}`}>{title}</p>
          {subtitle && <p className="truncate text-[11px] text-slate-500">{subtitle}</p>}
        </div>
        <div className="flex shrink-0 items-center">
          {download && (
            <IconButton label={`Download ${title}`} onClick={() => downloadResult(download)}>
              <Download className="h-3.5 w-3.5" aria-hidden />
            </IconButton>
          )}
          <IconButton label={`View ${title} fullscreen`} onClick={() => setOpen(true)}>
            <Maximize2 className="h-3.5 w-3.5" aria-hidden />
          </IconButton>
        </div>
      </figcaption>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="group relative flex items-center justify-center bg-slate-100"
        style={aspectRatio ? { aspectRatio: String(aspectRatio) } : undefined}
        aria-label={`Open ${title} fullscreen`}
      >
        <img
          src={src}
          alt={title}
          loading="lazy"
          className={`h-full w-full object-contain ${pixelated ? "img-pixelated" : ""}`}
          draggable={false}
        />
      </button>
      {(showLegend || footer) && (
        <div className={`flex flex-col gap-2 border-t border-slate-100 ${compact ? "px-2 py-1.5" : "px-3 py-2"}`}>
          {showLegend && legend && <ColorLegend legend={legend} compact={compact} />}
          {footer}
        </div>
      )}
      {open && (
        <FullscreenViewer
          src={src}
          title={title}
          subtitle={subtitle}
          legend={legend}
          pixelated={pixelated}
          onDownload={download ? () => downloadResult(download) : undefined}
          onClose={() => setOpen(false)}
        />
      )}
    </figure>
  );
}

interface FullscreenProps {
  src: string;
  title: string;
  subtitle?: string;
  legend?: ColorLegendData;
  pixelated: boolean;
  onDownload?: () => void;
  onClose: () => void;
}

const MIN_ZOOM = 1;
const MAX_ZOOM = 16;

function FullscreenViewer({ src, title, subtitle, legend, pixelated, onDownload, onClose }: FullscreenProps) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const drag = useRef<{ x: number; y: number; px: number; py: number } | null>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  const reset = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, []);
  const zoomBy = useCallback((factor: number) => {
    setZoom((z) => {
      const next = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, z * factor));
      if (next === 1) setPan({ x: 0, y: 0 });
      return next;
    });
  }, []);

  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      else if (e.key === "+" || e.key === "=") zoomBy(1.25);
      else if (e.key === "-") zoomBy(0.8);
      else if (e.key === "0") reset();
    };
    window.addEventListener("keydown", onKey);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = overflow;
    };
  }, [onClose, zoomBy, reset]);

  const onWheel = (e: WheelEvent<HTMLDivElement>) => zoomBy(e.deltaY < 0 ? 1.15 : 1 / 1.15);
  const onPointerDown = (e: PointerEvent<HTMLDivElement>) => {
    if (zoom === 1) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    drag.current = { x: e.clientX, y: e.clientY, px: pan.x, py: pan.y };
  };
  const onPointerMove = (e: PointerEvent<HTMLDivElement>) => {
    const d = drag.current;
    if (!d) return;
    setPan({ x: d.px + (e.clientX - d.x) / zoom, y: d.py + (e.clientY - d.y) / zoom });
  };
  const endDrag = () => {
    drag.current = null;
  };

  return (
    <div role="dialog" aria-modal="true" aria-label={title} className="fixed inset-0 z-50 flex flex-col bg-slate-950">
      <div className="flex items-center justify-between gap-3 border-b border-slate-800 px-4 py-2 text-slate-200">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium">{title}</p>
          {subtitle && <p className="truncate text-xs text-slate-400">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-1">
          <IconButton label="Zoom out" onClick={() => zoomBy(0.8)} className="text-slate-300 hover:bg-slate-800 hover:text-white">
            <Minus className="h-4 w-4" aria-hidden />
          </IconButton>
          <span className="num w-14 text-center text-xs text-slate-400">{Math.round(zoom * 100)}%</span>
          <IconButton label="Zoom in" onClick={() => zoomBy(1.25)} className="text-slate-300 hover:bg-slate-800 hover:text-white">
            <Plus className="h-4 w-4" aria-hidden />
          </IconButton>
          <IconButton label="Fit to screen" onClick={reset} className="text-slate-300 hover:bg-slate-800 hover:text-white">
            <RotateCcw className="h-4 w-4" aria-hidden />
          </IconButton>
          {onDownload && (
            <IconButton label="Download" onClick={onDownload} className="text-slate-300 hover:bg-slate-800 hover:text-white">
              <Download className="h-4 w-4" aria-hidden />
            </IconButton>
          )}
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            aria-label="Close fullscreen"
            className="ml-2 inline-flex h-7 w-7 items-center justify-center rounded text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        </div>
      </div>
      <div
        className={`relative flex-1 overflow-hidden ${zoom > 1 ? "cursor-grab active:cursor-grabbing" : ""}`}
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
        onDoubleClick={() => (zoom === 1 ? zoomBy(2) : reset())}
      >
        <img
          src={src}
          alt={title}
          draggable={false}
          className={`absolute inset-0 h-full w-full object-contain p-4 select-none ${pixelated || zoom > 2 ? "img-pixelated" : ""}`}
          style={{ transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`, transformOrigin: "center" }}
        />
      </div>
      {legend && (
        <div className="border-t border-slate-800 bg-white px-4 py-2">
          <div className="mx-auto max-w-xl">
            <ColorLegend legend={legend} />
          </div>
        </div>
      )}
      <p className="sr-only">Scroll or use plus and minus to zoom, drag to pan, 0 to fit, Escape to close.</p>
    </div>
  );
}
