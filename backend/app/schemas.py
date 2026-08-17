from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

PromptModel = Literal["chatgpt", "claude", "both"]
PromptLevel = Literal["standard", "professional", "expert"]


class Message(BaseModel):
    message: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    csrf_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=12, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    avatar_url: str | None
    is_admin: bool
    created_at: datetime


class UserUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    avatar_url: HttpUrl | None = None


class PromptStartRequest(BaseModel):
    brief: str = Field(min_length=3, max_length=8000)
    model_target: PromptModel = "chatgpt"
    level: PromptLevel = "professional"
    category: str = Field(default="other", min_length=2, max_length=50)
    tags: list[str] = Field(default_factory=list, max_length=10)


class PromptAnswersRequest(BaseModel):
    answers: dict[str, str] = Field(min_length=1)


class PromptUpdateRequest(BaseModel):
    content: str | None = Field(default=None, max_length=20000)
    tags: list[str] | None = Field(default=None, max_length=10)
    is_favorite: bool | None = None


class PromptAnalysis(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    quality_breakdown: dict[str, int] = Field(default_factory=dict)
    quality_explanation: str = ""


class PromptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    brief: str
    model_target: PromptModel
    level: PromptLevel
    category: str
    status: str
    questions: list[str]
    answers: dict[str, str]
    content: str | None
    quality_score: int | None
    analysis: PromptAnalysis = Field(default_factory=PromptAnalysis)
    tags: list[str]
    is_favorite: bool
    created_at: datetime
    updated_at: datetime


class PaginatedPrompts(BaseModel):
    items: list[PromptResponse]
    total: int


class DashboardResponse(BaseModel):
    total_prompts: int
    favorite_prompts: int
    generated_this_month: int
    average_quality_score: float | None
    recent_prompts: list[PromptResponse]


class AdminStatsResponse(BaseModel):
    users: int
    prompts: int
    generated_prompts: int
    active_last_30_days: int
