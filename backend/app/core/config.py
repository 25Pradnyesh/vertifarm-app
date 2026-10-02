import os
import json
from typing import List
from dotenv import load_dotenv

# Load local environment if available
load_dotenv()
load_dotenv("../.env")

class Settings:
    PROJECT_NAME: str = "VertiFarm Backend API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # CORS
    _raw_cors = os.getenv("CORS_ORIGINS", '["http://localhost:8081","http://localhost:8082","http://localhost:19006","*"]')
    try:
        CORS_ORIGINS: List[str] = json.loads(_raw_cors) if isinstance(_raw_cors, str) else _raw_cors
    except Exception:
        CORS_ORIGINS: List[str] = ["*"]
        
    # JWT & Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "vertifarm-dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # Google OAuth credentials
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_WEB_CLIENT_ID: str = os.getenv("GOOGLE_WEB_CLIENT_ID", os.getenv("EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID", ""))
    GOOGLE_IOS_CLIENT_ID: str = os.getenv("GOOGLE_IOS_CLIENT_ID", os.getenv("EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID", ""))
    GOOGLE_ANDROID_CLIENT_ID: str = os.getenv("GOOGLE_ANDROID_CLIENT_ID", os.getenv("EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID", ""))

    # Development Flags
    # When enabled, allows development tokens and test credentials for offline workflows
    ALLOW_DEV_AUTH: bool = os.getenv("ALLOW_DEV_AUTH", "true").lower() in ("true", "1", "yes")

    # Supabase / Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # MQTT Broker Configuration
    MQTT_ENABLED: bool = os.getenv("MQTT_ENABLED", "false").lower() in ("true", "1", "yes")
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_USERNAME: str = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD: str = os.getenv("MQTT_PASSWORD", "")
    MQTT_CLIENT_ID: str = os.getenv("MQTT_CLIENT_ID", "vertifarm-fastapi-backend")
    MQTT_TOPIC_PREFIX: str = os.getenv("MQTT_TOPIC_PREFIX", "vertifarm")
    MQTT_KEEPALIVE: int = int(os.getenv("MQTT_KEEPALIVE", "60"))

settings = Settings()
