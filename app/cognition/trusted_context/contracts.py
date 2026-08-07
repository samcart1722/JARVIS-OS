"""Infrastructure-free contracts for trusted request context resolution."""

from typing import Protocol

from app.cognition.trusted_context.models import (
    TrustedHostRequestInput,
    TrustedRequestContextResolution,
)


class TrustedRequestContextResolver(Protocol):
    def resolve(
        self,
        request: TrustedHostRequestInput,
    ) -> TrustedRequestContextResolution: ...
