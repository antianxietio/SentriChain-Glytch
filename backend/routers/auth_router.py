"""
Auth routes: register, login, me, update profile, onboarding.
"""

import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from database import get_db
from models import User, UserCompanyProfile
from auth import hash_password, verify_password, create_access_token, get_current_user
from schemas import OnboardRequest, OnboardResponse

auth_router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str
    role: str = "analyst"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in ("admin", "analyst"):
            raise ValueError("Role must be 'admin' or 'analyst'")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    current_password: str | None = None
    new_password: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    onboarded: bool = False


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@auth_router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    existing = db.query(User).filter(User.email == body.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=body.email.lower().strip(),
        full_name=body.full_name.strip(),
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user), onboarded=False)


@auth_router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and return a JWT."""
    user = db.query(User).filter(User.email == body.email.lower()).first()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    onboarded = db.query(UserCompanyProfile).filter(UserCompanyProfile.user_id == user.id).first() is not None
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user), onboarded=onboarded)


@auth_router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


@auth_router.patch("/me", response_model=UserResponse)
def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update name or password."""
    if body.full_name:
        current_user.full_name = body.full_name.strip()

    if body.new_password:
        if not body.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="current_password is required to set a new password",
            )
        if not verify_password(body.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )
        if len(body.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters",
            )
        current_user.hashed_password = hash_password(body.new_password)

    db.commit()
    db.refresh(current_user)
    return current_user


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------

def _profile_to_response(p: UserCompanyProfile) -> OnboardResponse:
    return OnboardResponse(
        id=p.id,
        user_id=p.user_id,
        company_name=p.company_name,
        company_type=p.company_type,
        raw_materials=json.loads(p.raw_materials),
        preferred_countries=json.loads(p.preferred_countries or "[]"),
        notes=p.notes,
        created_at=p.created_at,
    )


@auth_router.post("/onboard", response_model=OnboardResponse, status_code=status.HTTP_201_CREATED)
def create_onboard_profile(
    body: OnboardRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save company onboarding profile for the authenticated user."""
    existing = db.query(UserCompanyProfile).filter(UserCompanyProfile.user_id == current_user.id).first()
    if existing:
        # Update
        existing.company_name = body.company_name.strip()
        existing.company_type = body.company_type
        existing.raw_materials = json.dumps(body.raw_materials)
        existing.preferred_countries = json.dumps(body.preferred_countries)
        existing.notes = body.notes
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return _profile_to_response(existing)

    profile = UserCompanyProfile(
        user_id=current_user.id,
        company_name=body.company_name.strip(),
        company_type=body.company_type,
        raw_materials=json.dumps(body.raw_materials),
        preferred_countries=json.dumps(body.preferred_countries),
        notes=body.notes,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _profile_to_response(profile)


@auth_router.get("/onboard", response_model=OnboardResponse)
def get_onboard_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated user's company profile."""
    profile = db.query(UserCompanyProfile).filter(UserCompanyProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Onboarding profile not found")
    return _profile_to_response(profile)
