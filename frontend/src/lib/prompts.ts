export const categoryLabels: Record<string, string> = {
  programming: "Programowanie",
  marketing: "Marketing",
  business: "Biznes",
  copywriting: "Copywriting",
  seo: "SEO",
  science: "Nauka",
  law: "Prawo",
  medicine: "Medycyna",
  data_analysis: "Analiza danych",
  translation: "Tłumaczenia",
  education: "Edukacja",
  other: "Inne",
};

export const categoryOptions = Object.entries(categoryLabels);

export const promptStatusLabel = (status: string) => status === "generated" ? "Wygenerowany" : "Szkic — wymaga odpowiedzi";
