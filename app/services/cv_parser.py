from io import BytesIO
import re

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class CVParseError(ValueError):
    pass


TECHNOLOGY_TERMS = (
    "Angular", "AWS", "Azure", "C#", "C++", "CSS", "Dart", "Django", "Docker",
    ".NET", "FastAPI", "Flask", "Flutter", "GCP", "Git", "Go", "HTML",
    "Java", "JavaScript", "Jenkins", "Kotlin", "Kubernetes", "Laravel", "Linux",
    "MongoDB", "MySQL", "Node.js", "NumPy", "Pandas", "PHP", "Playwright",
    "PostgreSQL", "Python", "Pytest", "React", "Redis", "Rust", "Selenium",
    "Spring", "SQL", "Swift", "Terraform", "TypeScript", "Vue",
)


def suggest_technologies_from_text(text: str) -> list[dict[str, str]]:
    suggestions = []
    for name in TECHNOLOGY_TERMS:
        match = re.search(rf"(?<![\w]){re.escape(name)}(?![\w])", text, re.IGNORECASE)
        if match:
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 120)
            context = " ".join(text[start:end].split())
            suggestions.append({"name": name, "context": context[:300]})
    return suggestions


def extract_technology_suggestions(pdf_data: bytes) -> list[dict[str, str]]:
    try:
        reader = PdfReader(BytesIO(pdf_data), strict=False)
        if reader.is_encrypted:
            raise CVParseError("No se admiten PDF protegidos con contraseña.")
        if len(reader.pages) > 30:
            raise CVParseError("El CV no puede superar las 30 páginas.")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except CVParseError:
        raise
    except (PdfReadError, OSError, ValueError) as error:
        raise CVParseError("No se pudo leer el PDF; comprueba que no esté dañado.") from error

    return suggest_technologies_from_text(text)