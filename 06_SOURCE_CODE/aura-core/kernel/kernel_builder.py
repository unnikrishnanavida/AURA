from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from .kernel import Kernel


@dataclass
class KernelBuilder:
    """Fluent builder for creating a configured Kernel instance.

    Example:
        builder = KernelBuilder('my-kernel')
        kernel = (builder.with_config({...})
                        .with_component('logger', logger)
                        .build())
    """

    name: str = "aura-kernel"
    config: Dict[str, Any] = field(default_factory=dict)
    components: Dict[str, Any] = field(default_factory=dict)

    def with_config(self, config: Dict[str, Any]) -> "KernelBuilder":
        self.config.update(config)
        return self

    def with_component(self, key: str, component: Any) -> "KernelBuilder":
        self.components[key] = component
        return self

    def build(self) -> Kernel:
        kernel = Kernel(name=self.name, config=self.config)
        for k, v in self.components.items():
            kernel.register(k, v)
        return kernel
