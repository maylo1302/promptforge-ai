import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <section className={cn("surface p-5", className)} {...props} />;
}

export function CardTitle({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return <div className="mb-4 flex items-center justify-between gap-4"><h2 className="text-base font-bold">{children}</h2>{action}</div>;
}

