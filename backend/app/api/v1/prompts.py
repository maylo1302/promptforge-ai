from io import BytesIO
from fastapi import APIRouter, HTTPException, Query, Response
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from sqlalchemy import func, or_, select
from app.api.deps import CurrentUser, DbSession
from app.models import AuditLog, Prompt
from app.schemas import PaginatedPrompts, PromptAnswersRequest, PromptResponse, PromptStartRequest, PromptUpdateRequest
from app.services.prompt_engine import prompt_engine

router = APIRouter(prefix="/prompts", tags=["Prompty"])


def find_owned_prompt(db: DbSession, user_id: str, prompt_id: str) -> Prompt:
    prompt = db.scalar(select(Prompt).where(Prompt.id == prompt_id, Prompt.user_id == user_id))
    if prompt is None:
        raise HTTPException(status_code=404, detail="Nie znaleziono promptu.")
    return prompt


@router.post("", response_model=PromptResponse, status_code=201)
def start_prompt(payload: PromptStartRequest, db: DbSession, user: CurrentUser) -> Prompt:
    prompt = Prompt(brief=payload.brief.strip(), user_id=user.id, model_target=payload.model_target, level=payload.level, category=payload.category.lower(), tags=[tag.strip().lower() for tag in payload.tags if tag.strip()])
    questions = prompt_engine.clarification_questions(prompt.brief, prompt.category)
    prompt.questions = questions
    if questions:
        prompt.status = "needs_clarification"
    else:
        result = prompt_engine.generate(prompt)
        prompt.content, prompt.quality_score, prompt.analysis, prompt.status = result.content, result.score, result.analysis, "generated"
    db.add(prompt)
    db.flush()
    db.add(AuditLog(user_id=user.id, action="prompt.started", metadata_json={"prompt_id": prompt.id}))
    db.commit()
    db.refresh(prompt)
    return prompt


@router.post("/{prompt_id}/answers", response_model=PromptResponse)
def answer_questions(prompt_id: str, payload: PromptAnswersRequest, db: DbSession, user: CurrentUser) -> Prompt:
    prompt = find_owned_prompt(db, user.id, prompt_id)
    allowed = set(prompt.questions)
    accepted = {question: answer.strip() for question, answer in payload.answers.items() if question in allowed and answer.strip()}
    if not accepted:
        raise HTTPException(status_code=422, detail="Podaj odpowiedź na co najmniej jedno pytanie doprecyzowujące.")
    placeholders = prompt_engine.placeholder_answer_questions(accepted)
    if placeholders:
        raise HTTPException(status_code=422, detail="Jedna z odpowiedzi jest zbyt ogólna. Zamiast „ma działać” podaj konkretne narzędzie, regułę, ograniczenie albo kryterium sukcesu.")
    prompt.answers = {**prompt.answers, **accepted}
    unanswered = [question for question in prompt.questions if question not in prompt.answers]
    if unanswered:
        prompt.questions = unanswered
    else:
        result = prompt_engine.generate(prompt)
        prompt.content, prompt.quality_score, prompt.analysis, prompt.status = result.content, result.score, result.analysis, "generated"
    db.add(AuditLog(user_id=user.id, action="prompt.answered", metadata_json={"prompt_id": prompt.id}))
    db.commit()
    db.refresh(prompt)
    return prompt


@router.get("", response_model=PaginatedPrompts)
def list_prompts(db: DbSession, user: CurrentUser, search: str | None = None, category: str | None = None, favorite: bool | None = None, sort: str = Query("updated_at", pattern="^(updated_at|created_at|quality_score)$"), order: str = Query("desc", pattern="^(asc|desc)$"), page: int = Query(1, ge=1), page_size: int = Query(12, ge=1, le=100)) -> PaginatedPrompts:
    statement = select(Prompt).where(Prompt.user_id == user.id)
    if search:
        phrase = f"%{search.strip()}%"
        statement = statement.where(or_(Prompt.brief.ilike(phrase), Prompt.content.ilike(phrase)))
    if category:
        statement = statement.where(Prompt.category == category.lower())
    if favorite is not None:
        statement = statement.where(Prompt.is_favorite.is_(favorite))
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    column = getattr(Prompt, sort)
    statement = statement.order_by(column.asc() if order == "asc" else column.desc())
    items = list(db.scalars(statement.offset((page - 1) * page_size).limit(page_size)))
    return PaginatedPrompts(items=items, total=total)


@router.get("/{prompt_id}", response_model=PromptResponse)
def get_prompt(prompt_id: str, db: DbSession, user: CurrentUser) -> Prompt:
    return find_owned_prompt(db, user.id, prompt_id)


@router.patch("/{prompt_id}", response_model=PromptResponse)
def update_prompt(prompt_id: str, payload: PromptUpdateRequest, db: DbSession, user: CurrentUser) -> Prompt:
    prompt = find_owned_prompt(db, user.id, prompt_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(prompt, field, value)
    db.add(AuditLog(user_id=user.id, action="prompt.updated", metadata_json={"prompt_id": prompt.id}))
    db.commit()
    db.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}", status_code=204)
def delete_prompt(prompt_id: str, db: DbSession, user: CurrentUser) -> Response:
    prompt = find_owned_prompt(db, user.id, prompt_id)
    db.delete(prompt)
    db.add(AuditLog(user_id=user.id, action="prompt.deleted", metadata_json={"prompt_id": prompt_id}))
    db.commit()
    return Response(status_code=204)


def build_pdf(content: str) -> bytes:
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    x, y = 48, height - 52
    pdf.setTitle("PromptForge AI – eksport promptu")
    pdf.setFont("Helvetica", 10)
    for raw_line in content.splitlines():
        words = raw_line.split() or [""]
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if stringWidth(candidate, "Helvetica", 10) > width - 96:
                pdf.drawString(x, y, line.encode("latin-1", "replace").decode("latin-1"))
                y -= 14
                line = word
            else:
                line = candidate
        pdf.drawString(x, y, line.encode("latin-1", "replace").decode("latin-1"))
        y -= 14
        if y < 48:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = height - 52
    pdf.save()
    return output.getvalue()


@router.get("/{prompt_id}/export")
def export_prompt(prompt_id: str, db: DbSession, user: CurrentUser, format: str = Query("markdown", pattern="^(markdown|pdf)$")) -> Response:
    prompt = find_owned_prompt(db, user.id, prompt_id)
    if not prompt.content:
        raise HTTPException(status_code=409, detail="Prompt nie został jeszcze wygenerowany.")
    filename = f"promptforge-{prompt.id}"
    if format == "pdf":
        return Response(content=build_pdf(prompt.content), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'})
    return Response(content=prompt.content, media_type="text/markdown; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{filename}.md"'})
