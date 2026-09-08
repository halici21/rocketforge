"""Where a fluid property came from.

Recorded on the state itself rather than looked up later, for the reason Phase
5G established across the propulsion stack: a result must be able to say what
produced it without consulting anything that may since have changed.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .errors import FluidStateError

__all__ = ["FluidPropertyProvenance"]


@dataclass(frozen=True, slots=True)
class FluidPropertyProvenance:
    """The identity of the model that produced a fluid state.

    Attributes:
        provider_id: Short stable id, e.g. ``"coolprop"``, ``"constant"``.
        provider_label: Human-readable name for the interface.
        provider_version: The adapter's own version.
        library_version: The backing library's version, when there is one.
        backend: The equation-of-state backend or model family actually used,
            e.g. ``"HEOS"`` or ``"constant-property"``. Load-bearing: two
            backends of one library are two models.
        native_fluid_name: What the provider calls this fluid. Kept here, in the
            provenance, so it never has to appear in the domain.
        model_notes: Anything a later reader needs, such as the reference the
            constant values were taken from.
        approximations: Named approximations this model applies. A caller can
            show them; a test can assert one is present.
    """

    provider_id: str
    provider_label: str
    provider_version: str = ""
    library_version: str = ""
    backend: str = ""
    native_fluid_name: str = ""
    model_notes: str = ""
    approximations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("provider_id", "provider_label"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise FluidStateError(
                    f"fluid provenance {name} must be a non-empty string, "
                    f"got {value!r}. A property with no attributable source is "
                    "the hardest kind of number to check later.")
        if not isinstance(self.approximations, tuple):
            raise FluidStateError("approximations must be a tuple of strings")
        for item in self.approximations:
            if not isinstance(item, str) or not item.strip():
                raise FluidStateError(
                    f"approximation entries must be non-empty strings, got {item!r}")

    def as_mapping(self) -> Mapping[str, object]:
        """A read-only view for display and for the acceptance artifacts."""
        return MappingProxyType({
            "provider_id": self.provider_id,
            "provider_label": self.provider_label,
            "provider_version": self.provider_version,
            "library_version": self.library_version,
            "backend": self.backend,
            "native_fluid_name": self.native_fluid_name,
            "model_notes": self.model_notes,
            "approximations": self.approximations,
        })
