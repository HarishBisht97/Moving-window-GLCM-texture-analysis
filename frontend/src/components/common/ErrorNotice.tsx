import { AlertTriangle } from "lucide-react";

export function ErrorNotice({ title, message }: { title: string; message: string }) {
  return (
    <div role="alert" className="flex gap-2.5 rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-red-800">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <div>
        <p className="text-sm font-medium">{title}</p>
        <p className="mt-0.5 text-xs break-words">{message}</p>
      </div>
    </div>
  );
}
