import { ImageUp, Loader2 } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";

export const ACCEPTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".tif", ".tiff"];

interface DropZoneProps {
  onFile: (file: File) => void;
  busy: boolean;
  compact?: boolean;
}

function hasAcceptedExtension(name: string): boolean {
  const lower = name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

export function DropZone({ onFile, busy, compact = false }: DropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const accept = (file: File | undefined) => {
    if (!file) return;
    if (!hasAcceptedExtension(file.name)) {
      setLocalError(`Unsupported file type. Use ${ACCEPTED_EXTENSIONS.join(", ")}.`);
      return;
    }
    setLocalError(null);
    onFile(file);
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    if (!busy) accept(e.dataTransfer.files[0]);
  };

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload image: drop a file or press Enter to browse"
        aria-busy={busy}
        onClick={() => !busy && inputRef.current?.click()}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !busy) {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-md border border-dashed text-center transition-colors ${
          compact ? "px-4 py-6" : "px-6 py-16"
        } ${dragging ? "border-teal-600 bg-teal-50" : "border-slate-300 bg-slate-50 hover:border-slate-400 hover:bg-slate-100"}`}
      >
        {busy ? (
          <Loader2 className="h-8 w-8 animate-spin text-teal-700" aria-hidden />
        ) : (
          <ImageUp className="h-8 w-8 text-slate-400" aria-hidden />
        )}
        <p className="mt-3 text-sm font-medium text-slate-800">
          {busy ? "Uploading and reading image…" : "Drop a grayscale or RGB image here"}
        </p>
        {!busy && (
          <p className="mt-1 text-xs text-slate-500">
            or <span className="font-medium text-teal-700 underline underline-offset-2">browse files</span> · PNG, JPG/JPEG,
            TIFF/GeoTIFF
          </p>
        )}
        <p className="mt-2 text-[11px] text-slate-400">
          RGB is converted with Y = 0.299R + 0.587G + 0.114B; multiband images use the mean of their bands.
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS.join(",")}
        className="hidden"
        onChange={(e) => {
          accept(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
      {localError && <p className="mt-2 text-xs text-red-700">{localError}</p>}
    </div>
  );
}
