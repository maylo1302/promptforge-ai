from dataclasses import dataclass
from re import findall

from app.models import Prompt
from app.services.ai_providers import enhance_prompt


@dataclass(frozen=True)
class GenerationResult:
    content: str
    score: int
    analysis: dict[str, object]


@dataclass(frozen=True)
class TaskProfile:
    slug: str
    label: str
    role: str
    questions: tuple[tuple[str, str], ...]


class PromptEngine:
    """Turns a short brief into a task-specific prompt and a transparent input-quality score."""

    vague_terms = {"coś", "czegokolwiek", "pomóż", "zrób", "stwórz", "napisz"}
    generic_phrases = {"ma działać", "po prostu", "jakoś", "dobrze", "fajnie", "najlepiej", "wszystko", "szybko", "nie wiem", "dowolnie", "bez znaczenia"}
    stop_words = {"aby", "ale", "bardzo", "będzie", "być", "dla", "jest", "jaki", "jakie", "jako", "lub", "ma", "mnie", "moja", "moje", "oraz", "po", "przez", "się", "ten", "tego", "tej", "to", "wraz", "zostać"}
    evidence_groups = {
        "ograniczenia": ("limit", "budżet", "nie ", "bez ", "zgodn", "wyłącznie", "ryzyko"),
        "dane": ("dane", "plik", "api", "źródł", "baza", "dokument", "brief"),
        "termin": ("termin", "data", "tydzień", "miesiąc", "deadline", "do końca"),
        "przykład": ("np.", "przykład", "wzór", "referenc"),
        "sukces": ("kryter", "mierzal", "akceptac", "sukces", "kpi"),
    }
    format_markers = ("format", "tabel", "lista", "markdown", "json", "pdf", "slajd", "raport", "układ", "znacznik", "limit znak")
    audience_markers = ("dla ", "odbior", "klient", "użytkownik", "zespół", "początkują", "programist", "zarząd")
    category_roles = {
        "programming": "inżynierem oprogramowania",
        "marketing": "strategiem marketingowym",
        "business": "analitykiem biznesowym",
        "copywriting": "copywriterem",
        "seo": "specjalistą SEO",
        "science": "analitykiem naukowym",
        "law": "specjalistą od analizy prawnej",
        "medicine": "specjalistą komunikacji medycznej",
        "data_analysis": "analitykiem danych",
        "translation": "tłumaczem i redaktorem",
        "education": "projektantem materiałów edukacyjnych",
        "other": "specjalistą dopasowanym do opisanego zadania",
    }
    category_requirements = {
        "programming": (
            "Rozdziel zakres MVP od funkcji późniejszych etapów.",
            "Zdefiniuj użytkowników, przepływy, dane, integracje i granice systemu.",
            "Podaj kryteria akceptacji oraz testy dla najważniejszych scenariuszy.",
        ),
        "business": (
            "Oddziel problem biznesowy, decyzje, ryzyka i mierzalne rezultaty.",
            "Zaproponuj kolejne kroki wraz z właścicielem, terminem i kryterium akceptacji.",
        ),
        "marketing": (
            "Zdefiniuj personę, kanały, komunikat, budżet i mierniki kampanii.",
            "Przygotuj warianty do testu oraz sposób interpretacji wyników.",
        ),
        "data_analysis": (
            "Opisz źródła danych, jakość danych, metryki i ograniczenia interpretacji.",
            "Oddziel obserwacje od wniosków i wskaż, czego dane nie potwierdzają.",
        ),
        "copywriting": (
            "Oprzyj komunikat na realnej ofercie, odbiorcy, dowodach i jednym wezwaniu do działania.",
            "Dopasuj ton, długość i strukturę do wskazanego kanału publikacji.",
        ),
        "seo": (
            "Uwzględnij intencję wyszukiwania, odbiorcę, temat strony i możliwe zapytania użytkowników.",
            "Nie obiecuj pozycji w wynikach wyszukiwania; podaj mierzalne działania i sposób ich kontroli.",
        ),
        "law": (
            "Wskaż jurysdykcję, datę obowiązywania informacji i dokumenty, na których opiera się analiza.",
            "Oddziel informacje ogólne od porady prawnej i zaznacz kwestie wymagające konsultacji z prawnikiem.",
        ),
        "medicine": (
            "Podaj odbiorcę, cel edukacyjny, źródła oraz granice bezpiecznej informacji medycznej.",
            "Nie stawiaj diagnozy ani nie zastępuj konsultacji medycznej; wskaż objawy wymagające pilnej pomocy.",
        ),
        "translation": (
            "Zachowaj znaczenie, nazwy własne, terminologię i format źródła.",
            "Dopasuj rejestr języka do odbiorcy i oznacz fragmenty niejednoznaczne zamiast je zgadywać.",
        ),
        "education": (
            "Dopasuj materiał do poziomu uczestników, celu uczenia i dostępnego czasu.",
            "Zaproponuj ćwiczenie oraz mierzalny sposób sprawdzenia, czy cel został osiągnięty.",
        ),
        "science": (
            "Rozdziel pytanie badawcze, metodę, dane, ograniczenia i poziom pewności wniosków.",
            "Cytuj lub jasno wskaż źródła; nie przedstawiaj korelacji jako związku przyczynowego bez podstaw.",
        ),
    }
    profile_requirements = {
        "software_product": ("Rozdziel zakres MVP od funkcji późniejszych etapów oraz opisz użytkowników, dane, integracje i granice systemu.", "Dla kluczowych przepływów podaj kryteria akceptacji, uprawnienia i testy."),
        "marketing_campaign": ("Zdefiniuj personę, ofertę, kanały, budżet, ograniczenia i mierniki kampanii.", "Przygotuj warianty do testu oraz sposób interpretacji wyników."),
        "data_analysis": ("Opisz źródła danych, jakość danych, metryki i ograniczenia interpretacji.", "Oddziel obserwacje od wniosków i wskaż, czego dane nie potwierdzają."),
        "business_decision": ("Porównaj opcje względem celu, danych, ryzyk i ograniczeń.", "Dla każdej rekomendacji podaj właściciela, termin oraz miernik sukcesu."),
        "copywriting": ("Zbuduj przekaz na potwierdzonych korzyściach i dowodach, bez niezweryfikowanych obietnic.", "Zakończ jednym jasnym wezwaniem do działania dopasowanym do kanału."),
        "seo": ("Dopasuj strukturę do intencji wyszukiwania i pytań odbiorcy.", "Podaj mierzalne działania SEO bez obietnic konkretnej pozycji w wyszukiwarce."),
        "legal_analysis": ("Uwzględnij wskazaną jurysdykcję, stan faktyczny, dokumenty i datę analizy.", "Oddziel informację ogólną od porady prawnej i wskaż ryzyka wymagające konsultacji z prawnikiem."),
        "medical_information": ("Przekazuj wyłącznie bezpieczną, edukacyjną informację zgodną z podanym kontekstem.", "Nie stawiaj diagnozy ani nie zastępuj lekarza; wskaż sygnały wymagające pilnej konsultacji."),
        "translation": ("Zachowaj znaczenie, terminologię, nazwy własne i format źródła.", "Oznacz niejednoznaczności zamiast dopowiadać brakujący sens."),
        "education": ("Dopasuj wyjaśnienie, przykład i ćwiczenie do poziomu uczestników oraz czasu.", "Dodaj sposób sprawdzenia osiągnięcia celu nauki."),
        "science": ("Oddziel dane, metodę, obserwacje, wnioski i ograniczenia.", "Nie przedstawiaj korelacji jako przyczynowości bez podstaw w materiale źródłowym."),
        "generic": ("Oprzyj odpowiedź wyłącznie na potwierdzonych informacjach i oznacz niezbędne założenia.", "Zamień cel na sprawdzalne działania, ograniczenia i kryteria sukcesu."),
    }
    profile_result_sections = {
        "software_product": (
            "Zakres MVP i granice pierwszej wersji.",
            "Główne przepływy użytkownika oraz ich scenariusze wyjątkowe.",
            "Dane, integracje i model uprawnień.",
            "Kryteria akceptacji oraz plan testów kluczowych przepływów.",
        ),
        "marketing_campaign": (
            "Persona, oferta i komunikat oparty na potwierdzonych korzyściach.",
            "Plan kanałów z materiałem i celem dla każdego kanału.",
            "Budżet, harmonogram, ograniczenia i ryzyka wizerunkowe.",
            "Eksperymenty oraz mierniki wraz z progami decyzji.",
        ),
        "data_analysis": (
            "Pytanie decyzyjne, dane wejściowe i ich ograniczenia jakościowe.",
            "Metodykę, segmenty i metryki analizy.",
            "Wnioski odróżnione od obserwacji oraz stopień pewności.",
            "Rekomendację, wizualizacje i kolejne dane potrzebne do decyzji.",
        ),
        "business_decision": (
            "Kontekst decyzji, interesariuszy i niezmiennych ograniczeń.",
            "Porównanie realistycznych opcji z korzyściami, kosztami i ryzykami.",
            "Rekomendację wraz z uzasadnieniem i założeniami.",
            "Plan wdrożenia: właściciel, termin i miernik sukcesu.",
        ),
        "copywriting": (
            "Najważniejszy przekaz oparty na ofercie, odbiorcy i dowodach.",
            "Gotową treść we wskazanym tonie, kanale i długości.",
            "Warianty nagłówka lub wezwania do działania, jeśli są użyteczne.",
            "Listę twierdzeń wymagających potwierdzenia oraz sposób pomiaru reakcji.",
        ),
        "seo": (
            "Intencję wyszukiwania i segment odbiorców.",
            "Klaster tematów oraz priorytetowe frazy i pytania użytkowników.",
            "Proponowaną strukturę strony lub treści wraz z elementami on-page.",
            "Działania, mierniki, wartości docelowe i częstotliwość kontroli.",
        ),
        "legal_analysis": (
            "Zakres analizy, stan faktyczny, jurysdykcję i datę odniesienia.",
            "Ryzyka oraz istotne zapisy dokumentów, odróżnione od faktów niepotwierdzonych.",
            "Praktyczne pytania lub dalsze kroki wymagające konsultacji z prawnikiem.",
            "Wyraźne zastrzeżenie granic informacji ogólnej.",
        ),
        "medical_information": (
            "Bezpieczne wyjaśnienie dopasowane do celu i poziomu odbiorcy.",
            "Informacje oparte na wskazanych źródłach oraz ich ograniczenia.",
            "Sygnały alarmowe, granice samopomocy i sytuacje wymagające konsultacji.",
        ),
        "translation": (
            "Tłumaczenie zachowujące znaczenie, format i wskazany rejestr języka.",
            "Nazwy własne i terminologię zgodne z podanym glosariuszem.",
            "Krótką listę niejednoznaczności wymagających decyzji, tylko gdy wystąpią.",
        ),
        "education": (
            "Cel nauki i punkt wyjścia uczestników.",
            "Wyjaśnienie, przykład oraz ćwiczenie dopasowane do czasu i formy.",
            "Sposób sprawdzenia efektu nauki wraz z kryterium zaliczenia.",
        ),
        "science": (
            "Pytanie badawcze, materiał źródłowy i metodę analizy.",
            "Wyniki oddzielone od interpretacji, ograniczeń i niepewności.",
            "Wnioski możliwe do uzasadnienia oraz dalsze pytania badawcze.",
        ),
        "generic": (
            "Rezultat bezpośrednio użyteczny dla wskazanego odbiorcy.",
            "Konkretne kroki, dane wejściowe i ograniczenia.",
            "Założenia, ryzyka oraz sprawdzalne kryteria sukcesu.",
        ),
    }

    office_agent_profile = TaskProfile(
        slug="office_agent",
        label="agent pracy biurowej",
        role="architektem osobistych agentów pracy biurowej",
        questions=(
            ("narzedzia_dane", "Narzędzia i dane: Z jakich narzędzi (e-mail, kalendarz, dokumenty, zadania) agent ma korzystać i do jakich danych może mieć dostęp?"),
            ("rutyny", "Rutyny: Jakie powtarzalne obowiązki ma wykonywać codziennie lub cyklicznie? Podaj 2–3 przykłady."),
            ("autonomia", "Autonomia: Które działania agent może wykonywać sam, a które muszą zostać zatwierdzone przed wysłaniem, zmianą lub usunięciem?"),
            ("pamiec_prywatnosc", "Pamięć i prywatność: Co agent może zapamiętywać, jak długo oraz jakich danych wrażliwych nie wolno mu zapisywać ani ujawniać?"),
            ("bledy_sukces", "Błędy i sukces: Co agent ma zrobić przy braku danych lub błędzie oraz po czym poznasz, że działa poprawnie?"),
        ),
    )
    software_profile = TaskProfile(
        slug="software_product",
        label="produkt cyfrowy",
        role="architektem produktu i inżynierem oprogramowania",
        questions=(
            ("uzytkownicy", "Użytkownicy: Kto będzie korzystać z produktu i jakie zadanie ma wykonać w pierwszej wersji?"),
            ("mvp", "Zakres MVP: Jakie 3–5 funkcji są niezbędne na start, a co świadomie odkładamy na później?"),
            ("dane_integracje", "Dane i integracje: Jakie dane są przetwarzane oraz z jakimi systemami lub API produkt ma się łączyć?"),
            ("bezpieczenstwo", "Bezpieczeństwo: Kto ma dostęp do danych, jakie są ograniczenia prywatności i co wymaga autoryzacji?"),
            ("akceptacja", "Akceptacja: Po czym użytkownik i zespół poznają, że najważniejszy przepływ działa poprawnie?"),
        ),
    )
    marketing_profile = TaskProfile(
        slug="marketing_campaign",
        label="kampania marketingowa",
        role="strategiem kampanii marketingowych",
        questions=(
            ("persona", "Odbiorca: Do kogo mówimy, z jakim problemem i na jakim etapie decyzji?"),
            ("oferta", "Oferta: Co dokładnie promujemy, jaka jest główna korzyść i czym różni się od alternatyw?"),
            ("kanaly", "Kanały: Gdzie kampania ma się pojawić i jakie materiały są potrzebne dla każdego kanału?"),
            ("budzet", "Ograniczenia: Jaki jest budżet, termin oraz ograniczenia prawne lub wizerunkowe?"),
            ("metryki", "Sukces: Jakie mierniki i progi sukcesu będą decydować o kontynuacji lub zmianie kampanii?"),
        ),
    )
    data_profile = TaskProfile(
        slug="data_analysis",
        label="analiza danych",
        role="analitykiem danych i konsultantem decyzyjnym",
        questions=(
            ("pytanie", "Pytanie decyzyjne: Jaką konkretną decyzję ma wesprzeć analiza?"),
            ("zrodla", "Źródła: Jakie dane są dostępne, z jakiego okresu i jakie znasz ograniczenia ich jakości?"),
            ("metryki", "Metryki: Jakie wskaźniki, segmenty lub porównania są najważniejsze?"),
            ("odbiorca", "Odbiorca: Kto podejmie decyzję na podstawie analizy i jaki ma poziom wiedzy?"),
            ("format", "Rezultat: W jakiej formie ma być wynik — tabela, raport, wykresy czy rekomendacje z uzasadnieniem?"),
        ),
    )
    business_profile = TaskProfile(
        slug="business_decision",
        label="decyzja biznesowa",
        role="analitykiem biznesowym i doradcą decyzyjnym",
        questions=(
            ("decyzja", "Decyzja: Jaką konkretną decyzję ma wesprzeć rezultat i kto ją podejmie?"),
            ("interesariusze", "Interesariusze: Kogo dotknie decyzja i jakie są ich najważniejsze potrzeby lub obawy?"),
            ("dane", "Fakty i dane: Jakie dane, liczby, dokumenty lub obserwacje są dostępne?"),
            ("ograniczenia", "Ograniczenia: Jaki jest termin, budżet, ryzyko lub element, którego nie wolno zmienić?"),
            ("sukces", "Sukces: Po czym zmierzymy, że rekomendacja lub plan przyniósł oczekiwany rezultat?"),
        ),
    )
    copywriting_profile = TaskProfile(
        slug="copywriting",
        label="tekst perswazyjny",
        role="copywriterem i strategiem komunikacji",
        questions=(
            ("oferta", "Oferta: Co dokładnie promujesz, dla kogo i jaką konkretną korzyść oferujesz?"),
            ("odbiorca", "Odbiorca: Kim jest czytelnik, z jakim problemem przychodzi i co może go powstrzymywać?"),
            ("dowody", "Wiarygodność: Jakie fakty, liczby, opinie lub przykłady można bezpiecznie wykorzystać?"),
            ("ton", "Ton i kanał: Gdzie tekst będzie opublikowany, jak ma brzmieć i jakiej długości potrzebujesz?"),
            ("cta", "Działanie: Co odbiorca ma zrobić po przeczytaniu tekstu i skąd poznamy skuteczność?"),
        ),
    )
    seo_profile = TaskProfile(
        slug="seo",
        label="treść SEO",
        role="specjalistą SEO i strategiem treści",
        questions=(
            ("strona", "Strona i cel: Jakiej strony lub oferty dotyczy treść oraz jaki wynik biznesowy ma wspierać?"),
            ("intencja", "Intencja: Z jakim pytaniem lub potrzebą użytkownik ma trafić na tę treść?"),
            ("temat", "Temat i frazy: Jakie główne zagadnienie, frazy lub pytania odbiorców są istotne?"),
            ("konkurencja", "Kontekst rynkowy: Jakie strony, marki lub materiały są punktem odniesienia i czym chcemy się wyróżnić?"),
            ("metryki", "Pomiar: Jak zmierzymy efekt — ruch, widoczność, zapytania, sprzedaż lub inny wskaźnik?"),
        ),
    )
    legal_profile = TaskProfile(
        slug="legal_analysis",
        label="analiza prawna",
        role="specjalistą od analizy prawnej",
        questions=(
            ("sprawa", "Sprawa: Jaki jest stan faktyczny, pytanie prawne i oczekiwany rodzaj informacji?"),
            ("jurysdykcja", "Prawo właściwe: Jakiego kraju lub systemu prawnego dotyczy sprawa i na jaki dzień ma być aktualna analiza?"),
            ("dokumenty", "Materiały: Jakie umowy, pisma, przepisy lub fakty są dostępne i czego w nich szukamy?"),
            ("ryzyko", "Ryzyko: Jaka decyzja zależy od odpowiedzi i jakie konsekwencje należy szczególnie ocenić?"),
            ("format", "Rezultat: Czy potrzebujesz checklisty, analizy ryzyk, streszczenia dokumentu czy pytań do prawnika?"),
        ),
    )
    medical_profile = TaskProfile(
        slug="medical_information",
        label="informacja medyczna",
        role="specjalistą komunikacji medycznej opartej na dowodach",
        questions=(
            ("cel", "Cel: Czy potrzebujesz materiału edukacyjnego, wyjaśnienia wyniku, przygotowania do wizyty czy czegoś innego?"),
            ("odbiorca", "Odbiorca: Dla kogo powstaje informacja i jaki ma poziom wiedzy medycznej?"),
            ("kontekst", "Kontekst: Jakie objawy, wynik, rozpoznanie lub sytuacja są istotne — bez danych identyfikujących pacjenta?"),
            ("zrodla", "Źródła i zakres: Czy są wytyczne, materiały lub ograniczenia, których należy się trzymać?"),
            ("bezpieczenstwo", "Bezpieczeństwo: Jakie ryzyka, przeciwwskazania lub sygnały alarmowe należy wyraźnie uwzględnić?"),
        ),
    )
    translation_profile = TaskProfile(
        slug="translation",
        label="tłumaczenie",
        role="tłumaczem i redaktorem",
        questions=(
            ("jezyki", "Języki: Z jakiego języka na jaki język ma być tłumaczenie?"),
            ("odbiorca", "Odbiorca: Kto przeczyta tekst i w jakiej sytuacji będzie go używać?"),
            ("ton", "Rejestr: Jaki ma być ton — formalny, prawny, marketingowy, techniczny czy swobodny?"),
            ("terminologia", "Terminologia: Jakie nazwy własne, glosariusz lub zwroty muszą pozostać niezmienione?"),
            ("format", "Format: Czy trzeba zachować układ, znaczniki, tabelę, limity znaków lub inny format źródła?"),
        ),
    )
    education_profile = TaskProfile(
        slug="education",
        label="materiał edukacyjny",
        role="projektantem materiałów edukacyjnych",
        questions=(
            ("uczestnicy", "Uczestnicy: Dla kogo powstaje materiał, jaki ma poziom wyjściowy i czego już nie trzeba tłumaczyć?"),
            ("cel", "Cel nauki: Co uczestnik ma umieć wykonać lub wyjaśnić po zakończeniu materiału?"),
            ("zakres", "Zakres: Jakie treści, źródła lub przykłady muszą się znaleźć, a czego nie obejmujemy?"),
            ("czas", "Forma i czas: Ile czasu jest dostępne oraz czy ma to być lekcja, ćwiczenie, prezentacja czy test?"),
            ("ocena", "Sprawdzenie efektu: Jak zweryfikujemy, że uczestnik osiągnął cel?"),
        ),
    )
    science_profile = TaskProfile(
        slug="science",
        label="analiza naukowa",
        role="analitykiem naukowym",
        questions=(
            ("pytanie", "Pytanie badawcze: Co dokładnie chcemy wyjaśnić, porównać lub sprawdzić?"),
            ("material", "Materiał i dane: Jakie źródła, publikacje, dane lub obserwacje można wykorzystać?"),
            ("metoda", "Metoda: Jaką metodę analizy, kryteria doboru źródeł lub sposób porównania preferujesz?"),
            ("ograniczenia", "Ograniczenia: Jakie założenia, ryzyka błędu lub granice wnioskowania należy uwzględnić?"),
            ("format", "Rezultat: Czy potrzebujesz przeglądu literatury, hipotez, planu badania, analizy czy streszczenia?"),
        ),
    )
    generic_profile = TaskProfile(
        slug="generic",
        label="opisane zadanie",
        role="specjalistą dopasowanym do opisanego zadania",
        questions=(
            ("rezultat", "Rezultat i użycie: Co konkretnie ma powstać, kto go użyje i do jakiej decyzji lub działania?"),
            ("odbiorca", "Odbiorca: Dla kogo tworzysz rezultat i jaki ma poziom wiedzy lub potrzeby?"),
            ("kontekst", "Kontekst i dane: Jakie fakty, materiały, przykłady lub dane wejściowe są dostępne?"),
            ("ograniczenia", "Ograniczenia: Jaki jest termin, budżet, zakres, ryzyko lub rzecz, której nie wolno robić?"),
            ("format", "Format i sukces: Jak ma wyglądać rezultat oraz po czym sprawdzisz, że jest dobry?"),
        ),
    )

    def classify_task(self, brief: str, category: str) -> TaskProfile | None:
        text = brief.lower()
        # Rodzaj pracy ma pierwszeństwo przed tematyką materiału. Przykładowo
        # „przetłumacz prawny regulamin” jest tłumaczeniem, a „zbuduj aplikację
        # dla kancelarii” pozostaje zadaniem produktowym, a nie analizą prawną.
        if any(word in text for word in ("tłumacz", "przetłumacz", "translation", "język docelowy", "source language")):
            return self.translation_profile
        if (("biurow" in text or "administracyj" in text) and ("agent" in text or "asystent" in text)) or any(phrase in text for phrase in ("osobisty asystent", "agent do e-mail", "agent do mail")):
            return self.office_agent_profile
        if any(phrase in text for phrase in ("zbuduj aplikac", "stwórz aplikac", "utwórz aplikac", "zaprojektuj aplikac", "implementuj", "napisz api")):
            return self.software_profile
        if any(word in text for word in ("seo", "pozycjon", "słowo klucz", "fraza klucz", "intencja wyszukiwania")):
            return self.seo_profile
        if any(word in text for word in ("copy", "tekst sprzedaż", "landing page", "hasło reklam", "opis produktu")):
            return self.copywriting_profile
        if any(word in text for word in ("kampani", "reklam", "lead", "newsletter", "social media")):
            return self.marketing_profile
        if any(word in text for word in ("lekcj", "kurs", "uczni", "student", "szkoleni", "materiał edukacyj")):
            return self.education_profile
        has_standalone_api = "api" in findall(r"\w+", text)
        if any(word in text for word in ("aplikac", "strona internet", "system", "oprogramowanie")) or has_standalone_api:
            return self.software_profile
        if any(word in text for word in ("dashboard", "raport danych", "zbiór danych", "csv", "arkusz")) or ("analiz" in text and any(word in text for word in ("dane", "metryk", "sprzedaż", "kolumn", "tabela"))):
            return self.data_profile
        if any(word in text for word in ("badani", "hipotez", "literatur", "publikacj naukow", "eksperyment")):
            return self.science_profile
        if any(word in text for word in ("jurysdykc", "przepis", "umow", "pozew", "kodeks", "prawny")):
            return self.legal_profile
        if any(word in text for word in ("objaw", "pacjent", "diagnoz", "leczen", "zdrow", "medycz")):
            return self.medical_profile
        if any(word in text for word in ("decyzj", "strategi", "wdrożeni", "proces biznes", "rentowno", "operacyj")):
            return self.business_profile
        return {
            "programming": self.software_profile,
            "marketing": self.marketing_profile,
            "business": self.business_profile,
            "copywriting": self.copywriting_profile,
            "seo": self.seo_profile,
            "science": self.science_profile,
            "law": self.legal_profile,
            "medicine": self.medical_profile,
            "data_analysis": self.data_profile,
            "translation": self.translation_profile,
            "education": self.education_profile,
        }.get(category, self.generic_profile)

    def profile_topic_evidence(self, topic: str, text: str) -> bool:
        markers = {
            "narzedzia_dane": ("e-mail", "email", "outlook", "gmail", "kalendarz", "calendar", "dokument", "drive", "notion", "zadani", "dane", "kontakt", "folder"),
            "rutyny": ("codzien", "co tydzień", "cyklicz", "regular", "powtarzal", "rano", "ranka", "każdego", "piątek", "tygodniow", "miesięcz"),
            "autonomia": ("zatwierdz", "akceptac", "samodziel", "autonom", "przed wysłaniem", "zgoda"),
            "pamiec_prywatnosc": ("pamię", "histori", "przechow", "dane osobowe", "wrażliw", "rodo", "prywat"),
            "bledy_sukces": ("błąd", "brak danych", "niepewn", "powiadom", "eskal", "kryter", "sukces", "mierzal", "test"),
            "uzytkownicy": ("użytkownik", "klient", "zespół", "dla ", "właściciel", "administrator", "pracownik", "pracownic", "kierown", "operator", "magazynier", "gość", "kupując"),
            "mvp": ("mvp", "pierwsza wers", "funkcj", "zakres", "menu", "koszyk", "płatno", "logow", "rejestr", "zamów", "raport"),
            "dane_integracje": ("dane", "api", "integrac", "baza", "system", "stripe", "google", "zapier", "webhook", "csv"),
            "bezpieczenstwo": ("dostęp", "uprawnien", "bezpiecze", "prywat", "autoryzac", "alarm", "piln", "przeciwwskaz", "ryzyk"),
            "akceptacja": ("kryter", "akceptac", "test", "działa poprawnie", "potwierd", "scenariusz", "poprawnie"),
            "persona": ("persona", "odbior", "klient", "grupa", "dla ", "rodzic", "firma", "marka"),
            "oferta": ("oferta", "produkt", "korzy", "wyróż", "usług", "kurs", "cena"),
            "kanaly": ("kanał", "social", "e-mail", "newsletter", "google", "linkedin", "instagram", "facebook", "tiktok"),
            "budzet": ("budżet", "termin", "limit", "data", "zł", "pln", "dni", "tydzień", "miesiąc"),
            "metryki": ("kpi", "metryk", "konwers", "zasięg", "sprzedaż", "ruch", "ctr", "roi", "roas", "przych"),
            "pytanie": ("decyz", "pytanie", "sprawdzić", "porównać", "wybra", "czy"),
            "zrodla": ("źródł", "dane", "plik", "baza", "okres", "csv", "raport"),
            "odbiorca": ("odbior", "zarząd", "zespół", "klient", "dla ", "administrator", "użytkownik", "uczestni"),
            "format": self.format_markers,
            "decyzja": ("decyz", "wybra", "zatwierdz", "wdroż", "otworzy", "zamkn"),
            "interesariusze": ("interesarius", "zespół", "klient", "zarząd", "pracownik", "właściciel", "partner"),
            "dane": ("dane", "liczb", "raport", "dokument", "obserwac", "wskaźnik"),
            "ograniczenia": self.evidence_groups["ograniczenia"] + self.evidence_groups["termin"],
            "sukces": self.evidence_groups["sukces"] + ("wzrost", "spadek", "%", "cel", "target"),
            "dowody": ("badani", "opini", "liczb", "dowod", "przykład", "referenc", "certyfikat", "wynik"),
            "ton": ("formal", "swobod", "profesjonal", "technicz", "ton", "styl", "linkedin", "instagram"),
            "cta": ("kup", "zapis", "kontakt", "zamów", "wezwanie", "konwers", "klik"),
            "strona": ("strona", "serwis", "landing", "oferta", "produkt"),
            "intencja": ("intencj", "szuka", "pytanie", "problem", "potrzeb", "wybrać", "porad"),
            "temat": ("temat", "fraza", "słowo klucz", "keyword", "zagadnien", "krem", "poradnik"),
            "konkurencja": ("konkur", "alternatyw", "wyróż", "porówn"),
            "sprawa": ("spraw", "stan faktycz", "pytanie prawne", "sytuacj", "najem", "umow"),
            "jurysdykcja": ("polsk", "ue", "jurysdykc", "kraj", "prawo", "brytyj", "angiel"),
            "dokumenty": ("umow", "dokument", "pismo", "przepis", "regulamin"),
            "ryzyko": ("ryzyk", "konsekwenc", "odpowiedzial", "spór", "kara"),
            "cel": ("cel", "edukac", "wyjaśn", "przygot", "informacj", "naucz", "umie", "potrafi"),
            "kontekst": ("objaw", "wynik", "sytuacj", "rozpozn", "kontekst", "fakt", "materiał", "przykład", "problem"),
            "jezyki": ("polsk", "angiel", "niemiec", "hiszpań", "francus", "język"),
            "terminologia": ("termin", "glosarius", "nazwa własna", "marka"),
            "uczestnicy": ("uczni", "student", "dzieci", "uczestni", "poziom", "klasa"),
            "zakres": ("zakres", "temat", "źródł", "materiał", "obejm"),
            "czas": ("minut", "godzin", "lekcj", "czas", "warsztat"),
            "ocena": ("test", "quiz", "ocen", "sprawdz", "ćwiczen"),
            "material": ("dane", "źródł", "publikac", "artykuł", "obserwac"),
            "metoda": ("metod", "porówn", "analiz", "eksperyment", "dobór"),
            "rezultat": ("rezultat", "wynik", "stwórz", "przygotuj", "napisz", "zaprojektuj"),
        }
        return any(marker in text.lower() for marker in markers.get(topic, ()))

    def topic_answer(self, profile: TaskProfile, topic: str, answers: dict[str, str]) -> str:
        for question_topic, question in profile.questions:
            if question_topic == topic:
                return answers.get(question, "").strip()
        return ""

    def topic_is_covered(self, profile: TaskProfile, topic: str, brief: str, answers: dict[str, str]) -> bool:
        answer = self.topic_answer(profile, topic, answers)
        if (profile.slug, topic) in {("seo", "metryki"), ("marketing_campaign", "metryki"), ("business_decision", "sukces")}:
            return self.measurable_target_is_covered(answer or brief)
        if answer:
            if self.is_placeholder_answer(topic, answer):
                return False
            detail = self.answer_detail(answer)
            # Długa, lecz niepowiązana odpowiedź nie może zamknąć pytania o inną dziedzinę.
            return detail >= 0.14 and self.profile_topic_evidence(topic, answer)
        # Pojedyncze słowo (np. „codziennie”) nie jest jeszcze specyfikacją rutyny.
        # Uznajemy temat za opisany w samym briefie dopiero, gdy opis ma wyraźny kontekst.
        return len(self.meaningful_words(brief)) >= 15 and self.profile_topic_evidence(topic, brief)

    def measurable_target_is_covered(self, text: str) -> bool:
        """Success criteria need a metric and a numeric threshold, not only a desired direction."""
        normalized = text.lower()
        has_metric = any(marker in normalized for marker in ("ruch", "widocz", "pozycj", "klik", "sesj", "konwers", "sprzeda", "przych", "lead", "zapyt", "koszt", "marż", "czas", "retenc", "satysfakc", "nps", "churn", "zasięg", "ctr", "roi", "roas", "udział"))
        has_numeric_value = any(char.isdigit() for char in normalized)
        has_target = any(marker in normalized for marker in ("cel", "target", "docelow", "wzrost", "spadek", "minimum", "maksimum", "co najmniej", "próg", "%", "procent"))
        return has_metric and has_numeric_value and has_target

    def clarification_questions(self, brief: str, category: str, answers: dict[str, str] | None = None) -> list[str]:
        profile = self.classify_task(brief, category)
        current_answers = answers or {}
        missing = [question for topic, question in profile.questions if not self.topic_is_covered(profile, topic, brief, current_answers)]
        # Bardzo krótki lub ogólnikowy brief potrzebuje pełnego wywiadu w danej dziedzinie,
        # nawet jeśli przypadkowe słowo pasuje do jednego z tematów.
        if not current_answers and (len(self.meaningful_words(brief)) < 6 or self.generic_hits(brief)):
            return [question for _, question in profile.questions]
        return missing[:5]

    def meaningful_words(self, text: str) -> list[str]:
        return [word for word in findall(r"\w+", text.lower()) if len(word) > 2 and word not in self.stop_words]

    def generic_hits(self, text: str) -> int:
        return sum(text.lower().count(phrase) for phrase in self.generic_phrases)

    def is_placeholder_answer(self, question: str, answer: str) -> bool:
        normalized = " ".join(answer.lower().split())
        if not normalized or self.generic_hits(normalized):
            return True
        if normalized in {"tak", "nie", "nie wiem", "brak", "dowolnie", "dla mnie", "dla siebie", "ja", "wszyscy", "każdy"}:
            return True
        if any(phrase in normalized for phrase in ("odbiorcą jestem ja", "odbiorca to ja", "jestem ja", "tylko ja", "jak zwykle", "po swojemu")):
            return True
        words = self.meaningful_words(normalized)
        if not words:
            return True
        if len(words) == 1 and not any(char.isdigit() for char in normalized):
            return True
        return bool(set(words).issubset(self.vague_terms))

    def placeholder_answer_questions(self, answers: dict[str, str]) -> list[str]:
        return [question for question, answer in answers.items() if self.is_placeholder_answer(question, answer)]

    def answer_detail(self, answer: str) -> float:
        """Returns 0..1 for the informational density of one clarification answer."""
        if self.generic_hits(answer):
            return 0.0
        words = self.meaningful_words(answer)
        unique_words = len(set(words))
        evidence = sum(any(marker in answer.lower() for marker in markers) for markers in self.evidence_groups.values())
        evidence += int(any(marker in answer.lower() for marker in self.format_markers))
        evidence += int(any(marker in answer.lower() for marker in self.audience_markers))
        return min(1.0, unique_words / 12 + evidence * 0.18)

    def profile_answers(self, prompt: Prompt, profile: TaskProfile) -> dict[str, str]:
        answers = prompt.answers or {}
        return {topic: answers.get(question, "").strip() for topic, question in profile.questions}

    def office_quality_assessment(self, prompt: Prompt, profile: TaskProfile) -> tuple[int, dict[str, object]]:
        answers = self.profile_answers(prompt, profile)
        combined = " ".join([prompt.brief, *answers.values()]).lower()
        goal = min(15, 3 + min(10, len(self.meaningful_words(prompt.brief))) + (2 if any(char.isdigit() for char in prompt.brief) else 0))
        completion = sum(bool(answer) for answer in answers.values()) / len(profile.questions)
        detail = sum(self.answer_detail(answer) for answer in answers.values()) / len(profile.questions)
        answers_score = round(7 * completion + 8 * detail)

        tool_score = round(8 * self.profile_topic_evidence("narzedzia_dane", answers["narzedzia_dane"]) + 7 * any(marker in answers["narzedzia_dane"].lower() for marker in ("dane", "kontakt", "folder", "dokument", "kalendarz")))
        routines_score = 10 if self.profile_topic_evidence("rutyny", answers["rutyny"]) else 0
        autonomy_score = 12 if self.profile_topic_evidence("autonomia", answers["autonomia"]) else 0
        memory_score = round(6 * self.profile_topic_evidence("pamiec_prywatnosc", answers["pamiec_prywatnosc"]) + 6 * any(marker in answers["pamiec_prywatnosc"].lower() for marker in ("wrażliw", "rodo", "prywat", "dane osobowe")))
        resilience_score = round(6 * any(marker in answers["bledy_sukces"].lower() for marker in ("błąd", "brak danych", "niepewn", "powiadom", "eskal")) + 6 * any(marker in answers["bledy_sukces"].lower() for marker in ("kryter", "sukces", "mierzal", "test")))
        parameter_score = min(9, sum(any(marker in combined for marker in markers) for markers in self.evidence_groups.values()) * 2 + (3 if any(char.isdigit() for char in combined) else 0))
        placeholder_count = sum(self.is_placeholder_answer(question, answers[topic]) for topic, question in profile.questions)
        generic_penalty = min(35, max(self.generic_hits(combined) * 7, placeholder_count * 8))
        normalized_answers = [" ".join(self.meaningful_words(answer)) for answer in answers.values() if answer]
        duplicate_answers = max(0, len(normalized_answers) - len(set(normalized_answers)))
        repetition_penalty = min(12, duplicate_answers * 5)
        raw_score = goal + answers_score + tool_score + routines_score + autonomy_score + memory_score + resilience_score + parameter_score - generic_penalty - repetition_penalty
        score = max(0, min(100, raw_score))
        if placeholder_count:
            score = min(score, 45)

        breakdown = {
            "Cel i zakres": goal,
            "Odpowiedzi na pytania": answers_score,
            "Narzędzia i dostęp do danych": tool_score,
            "Rutyny i obowiązki": routines_score,
            "Zakres autonomii": autonomy_score,
            "Pamięć i prywatność": memory_score,
            "Błędy i kryteria sukcesu": resilience_score,
            "Konkretne parametry": parameter_score,
            "Kara za ogólniki": -generic_penalty,
            "Kara za powtórzenia": -repetition_penalty,
        }
        missing: list[str] = []
        weaknesses: list[str] = []
        missing_map = {
            "Narzędzia i dostęp do danych": "Narzędzia, zakres danych i poziom dostępu.",
            "Rutyny i obowiązki": "Cykliczne obowiązki z częstotliwością i przykładem rezultatu.",
            "Zakres autonomii": "Działania automatyczne oraz wymagające zatwierdzenia.",
            "Pamięć i prywatność": "Zasady pamięci, retencji i ochrony danych wrażliwych.",
            "Błędy i kryteria sukcesu": "Reakcje na błąd, brak danych i mierzalne testy akceptacyjne.",
        }
        thresholds = {"Cel i zakres": 12, "Odpowiedzi na pytania": 12, "Narzędzia i dostęp do danych": 12, "Rutyny i obowiązki": 8, "Zakres autonomii": 10, "Pamięć i prywatność": 10, "Błędy i kryteria sukcesu": 10, "Konkretne parametry": 6}
        for name in missing_map:
            if breakdown[name] < thresholds[name]:
                weaknesses.append(f"Do dopracowania: {name.lower()}.")
                missing.append(missing_map[name])
        if generic_penalty:
            weaknesses.append("Wykryto odpowiedź pozorną lub ogólnik; nie zastępuje ona konkretnego wymagania.")
        if repetition_penalty:
            weaknesses.append("Powtarzające się odpowiedzi nie wnoszą dodatkowego kontekstu.")
        strengths = [f"Dobrze opisano: {name.lower()}." for name, value in breakdown.items() if name in thresholds and value >= thresholds[name]]
        return score, {
            "strengths": strengths or ["Opis zawiera podstawowy cel agenta."],
            "weaknesses": weaknesses,
            "missing_information": missing,
            "suggestions": ["Podaj jeden rzeczywisty przykład zadania agenta od wejścia do rezultatu.", "Zamień opis „ma działać” na regułę, uprawnienie albo mierzalny test."],
            "quality_breakdown": breakdown,
            "quality_explanation": "To ocena kompletności specyfikacji agenta biurowego: narzędzi, danych, rutyn, autonomii, pamięci, prywatności, błędów i kryteriów sukcesu. Nie ocenia jakości odpowiedzi modelu AI.",
        }

    def profile_quality_assessment(self, prompt: Prompt, profile: TaskProfile) -> tuple[int, dict[str, object]]:
        """Score every non-office profile against its own domain questions, not a universal template."""
        answers = self.profile_answers(prompt, profile)
        coverage = {topic: self.topic_is_covered(profile, topic, prompt.brief, prompt.answers or {}) for topic, _ in profile.questions}
        covered_count = sum(coverage.values())
        coverage_ratio = covered_count / len(profile.questions)
        answered_values = [answer for answer in answers.values() if answer]
        answer_detail = sum(self.answer_detail(answer) for answer in answered_values) / len(answered_values) if answered_values else 0.0
        all_text = " ".join([prompt.brief, *answered_values]).lower()
        brief_words = self.meaningful_words(prompt.brief)
        evidence_count = sum(any(marker in all_text for marker in markers) for markers in self.evidence_groups.values())
        has_format = any(marker in all_text for marker in self.format_markers)
        has_numeric_value = any(char.isdigit() for char in all_text)
        placeholder_count = sum(self.is_placeholder_answer(question, answers[topic]) for topic, question in profile.questions)
        normalized_answers = [" ".join(self.meaningful_words(answer)) for answer in answered_values]
        duplicate_answers = max(0, len(normalized_answers) - len(set(normalized_answers)))

        goal_score = min(15, 3 + min(10, len(brief_words)) + (2 if len(set(brief_words)) >= 7 else 0))
        coverage_score = round(45 * coverage_ratio)
        detail_score = round(15 * answer_detail)
        specificity_score = min(15, evidence_count * 3 + (3 if has_format else 0) + (3 if has_numeric_value else 0))
        coherence_score = 10 if coverage_ratio == 1 and duplicate_answers == 0 else 5 if coverage_ratio >= 0.8 and duplicate_answers == 0 else 0
        generic_penalty = min(36, max(self.generic_hits(all_text) * 6, placeholder_count * 10))
        repetition_penalty = min(12, duplicate_answers * 5)
        raw_score = goal_score + coverage_score + detail_score + specificity_score + coherence_score - generic_penalty - repetition_penalty
        score = max(0, min(100, raw_score))
        if coverage_ratio < 0.8:
            score = min(score, 59)
        if placeholder_count:
            score = min(score, 45)

        topic_names = {topic: question.split(":", 1)[0] for topic, question in profile.questions}
        missing_topics = [topic_names[topic] for topic, is_covered in coverage.items() if not is_covered]
        breakdown = {
            "Cel i zakres": goal_score,
            f"Pokrycie wymagań: {profile.label}": coverage_score,
            "Konkretność odpowiedzi": detail_score,
            "Dane, ograniczenia i format": specificity_score,
            "Spójność odpowiedzi": coherence_score,
            "Kara za ogólniki": -generic_penalty,
            "Kara za powtórzenia": -repetition_penalty,
        }
        weaknesses = [f"Brakuje informacji: {name.lower()}." for name in missing_topics]
        if placeholder_count:
            weaknesses.append("Wykryto odpowiedź pozorną; nie zastępuje ona wymagania domenowego.")
        if duplicate_answers:
            weaknesses.append("Powtarzające się odpowiedzi nie zwiększają kompletności briefu.")
        strengths = [f"Dobrze opisano: {topic_names[topic].lower()}." for topic, is_covered in coverage.items() if is_covered]
        return score, {
            "strengths": strengths or [f"Rozpoznano zadanie: {profile.label}."],
            "weaknesses": weaknesses,
            "missing_information": missing_topics,
            "suggestions": [f"Dodaj dane potrzebne dla obszarów: {', '.join(missing_topics[:3]).lower()}." if missing_topics else "Dodaj jeden rzeczywisty przykład, który pozwoli zweryfikować rezultat.", "Zastąp ogólniki konkretnymi danymi, ograniczeniami lub kryteriami."],
            "quality_breakdown": breakdown,
            "quality_explanation": f"To ocena kompletności briefu dla obszaru: {profile.label}. Mierzy pokrycie wymagań domenowych, konkretność, dane, ograniczenia i spójność — nie ocenia jakości odpowiedzi modelu AI.",
        }

    def general_quality_assessment(self, prompt: Prompt) -> tuple[int, dict[str, object]]:
        brief = prompt.brief.strip()
        prompt_answers = prompt.answers or {}
        answers = [answer.strip() for answer in prompt_answers.values() if answer.strip()]
        all_text = " ".join([brief, *answers]).lower()
        brief_words = self.meaningful_words(brief)
        expected_answers = max(len(prompt.questions or []), len(answers), 1)
        completion_ratio = min(1.0, len(answers) / expected_answers)
        detail_ratio = sum(self.answer_detail(answer) for answer in answers) / len(answers) if answers else 0.0
        evidence_count = sum(any(marker in all_text for marker in markers) for markers in self.evidence_groups.values())
        has_format = any(marker in all_text for marker in self.format_markers)
        has_audience = any(marker in all_text for marker in self.audience_markers)

        goal = min(25, 4 + min(14, len(brief_words)) + (3 if len(set(brief_words)) >= 7 else 0) + (4 if any(char.isdigit() for char in brief) else 0))
        context = round(14 * completion_ratio + 11 * detail_ratio)
        constraints = min(20, evidence_count * 4 + (4 if any(char.isdigit() for char in all_text) else 0))
        format_score = 15 if has_format else 0
        audience_score = 10 if has_audience else 0
        normalized_answers = [" ".join(self.meaningful_words(answer)) for answer in answers]
        duplicate_answers = max(0, len(normalized_answers) - len(set(normalized_answers)))
        coherence = 0 if not answers else 3 if len(answers) == 1 else 5 if duplicate_answers == 0 else 1
        placeholder_count = sum(self.is_placeholder_answer(question, answer) for question, answer in prompt_answers.items())
        vagueness_penalty = min(36, max(self.generic_hits(all_text) * 6, placeholder_count * 10))
        repetition_penalty = min(12, duplicate_answers * 5)
        raw_score = goal + context + constraints + format_score + audience_score + coherence - vagueness_penalty - repetition_penalty
        score = max(0, min(100, raw_score))
        if placeholder_count:
            score = min(score, 45)

        breakdown = {
            "Cel i zakres": goal,
            "Odpowiedzi na pytania": context,
            "Konkretne dane i ograniczenia": constraints,
            "Format rezultatu": format_score,
            "Odbiorca": audience_score,
            "Spójność odpowiedzi": coherence,
            "Kara za ogólniki": -vagueness_penalty,
            "Kara za powtórzenia": -repetition_penalty,
        }
        thresholds = {"Cel i zakres": 18, "Odpowiedzi na pytania": 18, "Konkretne dane i ograniczenia": 12, "Format rezultatu": 12, "Odbiorca": 8, "Spójność odpowiedzi": 4}
        strengths = [name for name, value in breakdown.items() if name in thresholds and value >= thresholds[name]]
        weaknesses: list[str] = []
        missing: list[str] = []
        if context < 18:
            weaknesses.append("Odpowiedzi nie pokrywają jeszcze wszystkich pytań lub są zbyt krótkie.")
            missing.append("Dane wejściowe, przykłady albo szczegóły użycia rezultatu.")
        if constraints < 12:
            weaknesses.append("Brakuje konkretnych danych, ograniczeń albo kryteriów akceptacji.")
            missing.append("Termin, budżet, dane wejściowe lub mierzalne kryteria sukcesu.")
        if not has_format:
            weaknesses.append("Format oczekiwanego rezultatu nie jest jasno określony.")
            missing.append("Preferowany format, np. tabela, lista, JSON lub raport.")
        if not has_audience:
            weaknesses.append("Nie wskazano odbiorcy ani poziomu wiedzy.")
            missing.append("Odbiorca, jego cel i poziom zaawansowania.")
        if vagueness_penalty:
            weaknesses.append("Wykryto ogólnikowe sformułowania; obniżają przewidywalność wyniku.")
        if repetition_penalty:
            weaknesses.append("Część odpowiedzi się powtarza, więc nie wnosi nowego kontekstu.")
        return score, {
            "strengths": [f"Dobrze opisano: {name.lower()}." for name in strengths] or ["Brief zawiera podstawowy cel zadania."],
            "weaknesses": weaknesses,
            "missing_information": list(dict.fromkeys(missing)),
            "suggestions": ["Dodaj przykład poprawnego rezultatu.", "Zastąp ogólniki konkretnymi danymi, ograniczeniami lub kryteriami."],
            "quality_breakdown": breakdown,
            "quality_explanation": "To deterministyczna ocena kompletności opisu i odpowiedzi: cel, pokrycie pytań, dane, format, odbiorca i spójność. Nie jest oceną jakości odpowiedzi modelu AI.",
        }

    def quality_assessment(self, prompt: Prompt) -> tuple[int, dict[str, object]]:
        profile = self.classify_task(prompt.brief, prompt.category)
        if profile and profile.slug == "office_agent":
            return self.office_quality_assessment(prompt, profile)
        if profile:
            profile_questions = {question for _, question in profile.questions}
            current_questions = prompt.questions or []
            if (not current_questions and not prompt.answers) or any(question in profile_questions for question in current_questions):
                return self.profile_quality_assessment(prompt, profile)
        return self.general_quality_assessment(prompt)

    def answer_for_topic(self, prompt: Prompt, profile: TaskProfile, topic: str) -> str:
        for question_topic, question in profile.questions:
            if question_topic == topic:
                return (prompt.answers or {}).get(question, "Nie podano.").strip() or "Nie podano."
        return "Nie podano."

    def build_office_agent_prompt(self, prompt: Prompt, profile: TaskProfile, model_label: str) -> str:
        tools = self.answer_for_topic(prompt, profile, "narzedzia_dane")
        routines = self.answer_for_topic(prompt, profile, "rutyny")
        autonomy = self.answer_for_topic(prompt, profile, "autonomia")
        memory = self.answer_for_topic(prompt, profile, "pamiec_prywatnosc")
        resilience = self.answer_for_topic(prompt, profile, "bledy_sukces")
        return f"""# Specyfikacja agenta pracy biurowej dla {model_label}

## Rola i cel
Jesteś {profile.role}. Zaprojektuj osobistego agenta do codziennej pracy biurowej na podstawie poniższej specyfikacji. Nie dopisuj niepotwierdzonych integracji, uprawnień ani automatyzacji.

**Cel użytkownika:** {prompt.brief.strip()}

## Uzgodniona specyfikacja
- **Narzędzia i dane:** {tools}
- **Cykliczne obowiązki:** {routines}
- **Zakres autonomii i zatwierdzeń:** {autonomy}
- **Pamięć i prywatność:** {memory}
- **Błędy i kryteria sukcesu:** {resilience}

## Zasady projektowania agenta
1. Zanim agent wykona działanie zewnętrzne (wysłanie wiadomości, utworzenie wydarzenia, zmianę dokumentu lub zadania), sprawdza swoje uprawnienia i zasady zatwierdzania.
2. Agent rozdziela działania na: automatyczne, wymagające akceptacji oraz zabronione. Nie zgaduje brakujących danych ani odbiorcy wiadomości.
3. Pamięta wyłącznie informacje dozwolone w specyfikacji; dla danych wrażliwych stosuje minimalny zakres dostępu i nie ujawnia ich w podsumowaniach.
4. Przy błędzie, konflikcie terminu lub braku danych zatrzymuje ryzykowne działanie, opisuje problem, proponuje bezpieczny następny krok i prosi o decyzję, jeśli jest potrzebna.

## Przygotuj rezultat w tej kolejności
1. **Zakres MVP** — cele, użytkownik, granice i funkcje nieobjęte pierwszą wersją.
2. **Codzienne przepływy pracy** — dla każdego obowiązku: sygnał startu, dane wejściowe, kroki, wynik, właściciel zatwierdzenia i sytuacje wyjątkowe.
3. **Integracje oraz model uprawnień** — narzędzie, dozwolone odczyty/zapisy, zakres danych i wymagane potwierdzenie.
4. **Model pamięci** — co zapamiętywać, przez jaki czas, jak użytkownik może to sprawdzić lub usunąć.
5. **Obsługa błędów i braków danych** — konkretne reakcje, komunikaty dla użytkownika i zasady eskalacji.
6. **Mierzalne testy akceptacyjne** — minimum pięć scenariuszy w formacie: warunek początkowy → działanie agenta → oczekiwany rezultat → kryterium zaliczenia.

## Jakość odpowiedzi
- Każdy przepływ musi odwoływać się do podanych narzędzi i zasad autonomii.
- Oznacz założenia oraz elementy, których nie da się zaprojektować bez dalszych danych.
- Stawiaj na konkretne reguły i testowalne zachowania, nie na ogólne deklaracje typu „ma działać”.
"""

    def build_general_prompt(self, prompt: Prompt, model_label: str, level_label: str, profile: TaskProfile | None) -> str:
        context = "\n".join(f"- {question}: {answer}" for question, answer in (prompt.answers or {}).items()) or "- Brak dodatkowych odpowiedzi."
        role = profile.role if profile else self.category_roles.get(prompt.category, self.category_roles["other"])
        profile_slug = profile.slug if profile else "generic"
        requirements = self.profile_requirements.get(profile_slug, self.category_requirements.get(prompt.category, ("Zamień cel na konkretne kroki, dane wejściowe, ograniczenia i kryteria akceptacji.")))
        domain_requirements = "\n".join(f"- {item}" for item in requirements)
        result_sections = self.profile_result_sections.get(profile_slug, self.profile_result_sections["generic"])
        result_outline = "\n".join(f"{index}. **{section}**" for index, section in enumerate(result_sections, start=1))
        return f"""# Prompt dla {model_label}

## Rola i cel
Jesteś {role}. Pracujesz na poziomie {level_label}.

**Cel:** {prompt.brief.strip()}

## Kontekst potwierdzony przez użytkownika
{context}

## Wymagania właściwe dla tego typu zadania
{domain_requirements}

## Zasady jakości
1. Opieraj się wyłącznie na potwierdzonych faktach. Każde niezbędne założenie oznacz wyraźnie.
2. Nie zastępuj szczegółów ogólnymi poradami; używaj danych, ograniczeń i kryteriów właściwych dla tego zadania.
3. Jeśli brakuje danych krytycznych, podaj bezpieczny wariant oraz jedno precyzyjne pytanie, które odblokuje decyzję.

## Oczekiwany rezultat
{result_outline}
"""

    def generate(self, prompt: Prompt) -> GenerationResult:
        model_label = {"chatgpt": "ChatGPT", "claude": "Claude", "both": "ChatGPT lub Claude"}[prompt.model_target]
        level_label = {"standard": "standardowym", "professional": "profesjonalnym", "expert": "eksperckim"}[prompt.level]
        profile = self.classify_task(prompt.brief, prompt.category)
        content = self.build_office_agent_prompt(prompt, profile, model_label) if profile and profile.slug == "office_agent" else self.build_general_prompt(prompt, model_label, level_label, profile)
        content = enhance_prompt(content, prompt.model_target)
        score, analysis = self.quality_assessment(prompt)
        return GenerationResult(content=content, score=score, analysis=analysis)


prompt_engine = PromptEngine()
