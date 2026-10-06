import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: "sm" | "md" | "lg";
  icon?: ReactNode;
}

const VARIANTS: Record<Variant, string> = {
  primary: "bg-teal-700 text-white hover:bg-teal-800 disabled:bg-slate-300 disabled:text-slate-500",
  secondary:
    "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 disabled:text-slate-400",
  ghost: "text-slate-600 hover:bg-slate-100 hover:text-slate-900 disabled:text-slate-300",
};

const SIZES = {
  sm: "h-7 px-2 text-xs gap-1.5",
  md: "h-8 px-3 text-sm gap-2",
  lg: "h-10 px-4 text-sm gap-2 font-semibold",
};

export function Button({ variant = "secondary", size = "md", icon, children, className = "", ...rest }: ButtonProps) {
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center rounded-md font-medium transition-colors disabled:cursor-not-allowed ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...rest}
    >
      {icon}
      {children}
    </button>
  );
}

export function IconButton({ label, children, className = "", ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={`inline-flex h-7 w-7 items-center justify-center rounded text-slate-500 hover:bg-slate-100 hover:text-slate-900 ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
