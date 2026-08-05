import { Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

export function Logo({ link = true }: { link?: boolean }) {
  const content = <><span className="grid size-8 place-items-center rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white shadow-md shadow-violet-500/30"><Sparkles size={16} /></span><span className="text-lg font-black tracking-tight">Prompt<span className="text-violet-600 dark:text-violet-400">Forge</span></span></>;
  return link ? <Link to="/" className="flex items-center gap-2.5">{content}</Link> : <div className="flex items-center gap-2.5">{content}</div>;
}

