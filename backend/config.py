"""
Environment & Configuration loader for BRAG Lead Hunter.
Reads .env in project root and falls back to ../instagram-lead-finder/.env for APIFY_TOKEN.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_dotenv_file(filepath: Path) -> None:
    if not filepath.exists():
        return
    try:
        for raw_line in filepath.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    except Exception:
        pass


_load_dotenv_file(BASE_DIR / ".env")
_load_dotenv_file(BASE_DIR / ".env.local")
# Reaproveita credenciais do projeto anterior instagram-lead-finder se disponíveis
_load_dotenv_file(BASE_DIR.parent / "instagram-lead-finder" / ".env")
_load_dotenv_file(BASE_DIR.parent / "instagram-lead-finder" / ".env.local")


def get_config() -> dict:
    db_rel = os.environ.get("DB_PATH", "data/brag_lead_hunter.db")
    db_path = Path(db_rel) if Path(db_rel).is_absolute() else (BASE_DIR / db_rel)
    legacy_rel = os.environ.get(
        "LEGACY_IG_LEADS_PATH",
        str(BASE_DIR.parent / "instagram-lead-finder" / "data" / "leads.json"),
    )
    legacy_path = Path(legacy_rel) if Path(legacy_rel).is_absolute() else (BASE_DIR / legacy_rel)

    return {
        "port": int(os.environ.get("PORT", "8090")),
        "db_path": str(db_path),
        "google_places_api_key": os.environ.get("GOOGLE_PLACES_API_KEY", "").strip(),
        "apify_token": os.environ.get("APIFY_TOKEN", "").strip(),
        "brag_crm_api_url": os.environ.get("BRAG_CRM_API_URL", "http://localhost:3000").strip(),
        "brag_crm_api_key": os.environ.get("BRAG_CRM_API_KEY", "").strip(),
        "legacy_ig_leads_path": str(legacy_path),
    }
