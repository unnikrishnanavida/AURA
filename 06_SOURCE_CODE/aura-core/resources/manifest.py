from dataclasses import dataclass
from typing import List


@dataclass
class Manifest:
    assets: List[str]
