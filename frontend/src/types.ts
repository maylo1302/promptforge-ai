export type PromptTarget = "chatgpt" | "claude" | "both";
export type PromptLevel = "standard" | "professional" | "expert";

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  avatar_url: string | null;
  is_admin: boolean;
  created_at: string;
}

export interface Analysis {
  strengths: string[];
  weaknesses: string[];
  missing_information: string[];
  suggestions: string[];
  quality_breakdown: Record<string, number>;
  quality_explanation: string;
}

export interface Prompt {
  id: string;
  brief: string;
  model_target: PromptTarget;
  level: PromptLevel;
  category: string;
  status: "needs_clarification" | "generated";
  questions: string[];
  answers: Record<string, string>;
  content: string | null;
  quality_score: number | null;
  analysis: Analysis;
  tags: string[];
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
}

export interface DashboardData {
  total_prompts: number;
  favorite_prompts: number;
  generated_this_month: number;
  average_quality_score: number | null;
  recent_prompts: Prompt[];
}
