from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address.", example="fan@example.com")
    password: str = Field(
        ...,
        min_length=8,
        description="User password with at least 8 characters.",
        example="Test12345!",
    )


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address.", example="fan@example.com")
    password: str = Field(
        ...,
        min_length=8,
        description="User password with at least 8 characters.",
        example="Test12345!",
    )


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT bearer token for authenticated API calls.")
    token_type: str = Field("bearer", description="Authentication scheme returned by the API.")
