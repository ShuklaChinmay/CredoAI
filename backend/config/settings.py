from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ❌ OLD (optional: remove ya ignore)
    DATABASE_URL:       str = ""
    DATABASE_URL_LOANS: str = ""

    MONGO_URI: str 

    SECRET_KEY:                    str = "dev-secret-key-change-in-production"
    ALGORITHM:                     str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:   int = 1440

    OPENROUTER_API_KEY:   str = ""
    OPENROUTER_BASE_URL:  str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL:     str = "openai/gpt-4o-mini"
    OPENROUTER_SITE_URL:  str = "http://localhost:5173"
    OPENROUTER_SITE_NAME: str = "CredoAI"

    UPI_VPA:         str = "loanai@ybl"
    UPI_PAYEE_NAME:  str = "CredoAI"
    DOC_FEE_INR:     int = 199

    RAZORPAY_KEY_ID:      str = ""
    RAZORPAY_KEY_SECRET:  str = ""

    SMTP_HOST:           str = "smtp.gmail.com"
    SMTP_PORT:           int = 587
    SMTP_USER:           str = ""
    SMTP_PASS:           str = ""
    OTP_EXPIRY_MINUTES:  int = 10

    FRONTEND_URL: str = "http://localhost:5173"
    APP_NAME:     str = "CredoAI"
    DEBUG:        bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()