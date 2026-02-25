from dataclasses import dataclass
import os


def _as_bool(v: str | None, default: bool) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ProjectConfig:
    monthly_budget_usd: int = int(os.getenv("MATHFOUNDRY_BUDGET_CAP_USD", "300"))
    arxiv_primary_category: str = os.getenv("MATHFOUNDRY_ARXIV_CATEGORY", "math.AG")
    strict_abstain: bool = _as_bool(os.getenv("MATHFOUNDRY_STRICT_ABSTAIN"), True)
    max_raw_files: int = int(os.getenv("MATHFOUNDRY_MAX_RAW_FILES", "200"))
    max_results_per_ingest: int = int(os.getenv("MATHFOUNDRY_MAX_RESULTS_PER_INGEST", "100"))
    data_dir: str = os.getenv("MATHFOUNDRY_DATA_DIR", "./data")


CONFIG = ProjectConfig()
