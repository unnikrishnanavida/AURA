from dataclasses import dataclass


@dataclass
class CacheStatistics:
    hits: int = 0
    misses: int = 0
