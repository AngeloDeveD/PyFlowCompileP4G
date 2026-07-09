from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScriptSource:
    """Description of the original script source used by a project.

    A source can point to an existing .bf file that will be imported and patched,
    or it can be empty when the project creates a brand-new script from Python.
    User code normally creates ScriptSource through BF(...) or Empty(...).
    """

    path: Path | None = None
    import_path: str | None = None
    target_path: str | None = None
    copy: bool = True

    @property
    def empty(self) -> bool:
        """Return True when the project has no original .bf file to import."""
        return self.path is None


def _normalize_target_path(target: str | None) -> str | None:
    """Return one canonical slash-separated target path.

    Build manifests and package layouts use forward slashes even on Windows, so
    every public helper funnels target paths through this function.
    """
    if target is None:
        return None
    return target.replace("\\", "/")


def BF(
    path: str | Path,
    *,
    import_path: str | None = None,
    target: str | None = None,
    copy: bool = True,
) -> ScriptSource:
    """Use an existing .bf file as the base for a patch build.

    Use this when the mod hooks or replaces procedures from an existing game
    script. The file at path is imported into the generated .flow. If target is
    provided, it is written into the manifest as the intended in-game output path,
    for example data_e.cpk/field/script/f007.bf.
    """
    source_path = Path(path)
    return ScriptSource(
        path=source_path,
        import_path=(import_path or source_path.name).replace("\\", "/"),
        target_path=_normalize_target_path(target),
        copy=copy,
    )


def Empty(*, target: str | None = None) -> ScriptSource:
    """Create a project without an original .bf file.

    Use this when the SDK should build a new standalone script from the Python
    procedures you define. If target is provided, it is written into the manifest
    as the intended in-game output path.
    """
    return ScriptSource(
        path=None,
        target_path=_normalize_target_path(target),
    )


def field_target(script_name: str, *, archive: str = "data_e.cpk") -> str:
    """Return the standard P4G field-script target path for one script name.

    Example:
        field_target("f007") -> "data_e.cpk/field/script/f007.bf"

    The helper exists so beginners do not have to remember or repeatedly type
    the full field-script directory layout by hand.
    """
    script = script_name.removesuffix(".bf")
    return f"{archive}/field/script/{script}.bf"


def event_target(script_name: str, *, archive: str = "data_e.cpk") -> str:
    """Return the standard P4G event-script target path for one script name.

    Example:
        event_target("E860_074A") -> "data_e.cpk/event_data/script/E860_074A.bf"
    """
    script = script_name.removesuffix(".bf")
    return f"{archive}/event_data/script/{script}.bf"


def FieldBF(
    script_name: str,
    path: str | Path,
    *,
    import_path: str | None = None,
    archive: str = "data_e.cpk",
    copy: bool = True,
) -> ScriptSource:
    """Patch helper for a standard P4G field script.

    This is the field-specific equivalent of BF(...). The helper fills the
    target path automatically, so user code only needs the script name and the
    original `.bf` path.
    """
    return BF(
        path,
        import_path=import_path,
        target=field_target(script_name, archive=archive),
        copy=copy,
    )


def FieldEmpty(script_name: str, *, archive: str = "data_e.cpk") -> ScriptSource:
    """Create helper for a brand-new P4G field script.

    This is the field-specific equivalent of Empty(...). It keeps the common
    `data_e.cpk/field/script/...` layout out of beginner code.
    """
    return Empty(target=field_target(script_name, archive=archive))


def EventBF(
    script_name: str,
    path: str | Path,
    *,
    import_path: str | None = None,
    archive: str = "data_e.cpk",
    copy: bool = True,
) -> ScriptSource:
    """Patch helper for a standard P4G event script."""
    return BF(
        path,
        import_path=import_path,
        target=event_target(script_name, archive=archive),
        copy=copy,
    )


def EventEmpty(script_name: str, *, archive: str = "data_e.cpk") -> ScriptSource:
    """Create helper for a brand-new P4G event script."""
    return Empty(target=event_target(script_name, archive=archive))
