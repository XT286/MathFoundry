from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectConfig:
    monthly_budget_usd: int = 300
    arxiv_primary_category: str = "math.AG"
    strict_abstain: bool = True


CONFIG = ProjectConfig()
