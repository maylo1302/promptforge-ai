import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));

export const formatDate = (value: string) => new Intl.DateTimeFormat("pl-PL", { dateStyle: "medium" }).format(new Date(value));

