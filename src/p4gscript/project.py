from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TYPE_CHECKING

from .bit_registry import DEFAULT_MOD_BIT_END, DEFAULT_MOD_BIT_START, BitReservation, allocate_bit
from .compiler import CompileResult, CompilerConfig, compile_flow
from .exceptions import DuplicateNameError, RenderError
from .flow import FlowDocument, Procedure
from .ids import BitId
from .msg import Message, MessageDocument, Selection, resolve_bustup
from .safety import normalize_safety
from .source import BF, Empty, ScriptSource, event_target, field_target

if TYPE_CHECKING:
    from .builder import BuildResult


@dataclass(frozen=True)
class ProjectImport:
    """One file imported by the generated FlowScript project.

    The SDK records both the source path on disk and the path written into the
    .flow import(...) statement. Build manifests use the same object to explain
    which original files were copied into the build directory.
    """

    source: str
    import_path: str
    kind: str
    copy: bool = True

    def to_dict(self) -> dict[str, str | bool]:
        """Return a JSON-serializable representation for build manifests."""
        return {
            "source": self.source,
            "import_path": self.import_path,
            "kind": self.kind,
            "copy": self.copy,
        }


@dataclass
class P4GProject:
    """Main object used to generate a P4G .flow/.msg/.bf mod project.

    Create one P4GProject per script you want to build. Add messages,
    procedures, hooks, and bit reservations to it, then call Build(). The source
    argument controls whether the project creates a new script with Empty(...) or
    patches an existing .bf with BF(...).
    """

    name: str
    encoding: str = "P4G_EFIGS"
    library: str = "P4G"
    out_format: str = "V1"
    safety: str = "standard"
    create_script: bool = True
    source: ScriptSource | str | Path | None = None
    bit_range_start: int = DEFAULT_MOD_BIT_START
    bit_range_end: int = DEFAULT_MOD_BIT_END
    analyzer: Any | None = None
    messages: list[Message] = field(default_factory=list)
    selections: list[Selection] = field(default_factory=list)
    procedures: list[Procedure] = field(default_factory=list)
    constants: list[str] = field(default_factory=list)
    bit_constants: dict[str, int] = field(default_factory=dict)
    bit_reservations: dict[str, BitReservation] = field(default_factory=dict)
    imports: list[ProjectImport] = field(default_factory=list)
    target_path: str | None = None
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.safety = normalize_safety(self.safety)
        if self.source is not None:
            self.use(self.source)

    @classmethod
    def new_script(
        cls,
        name: str,
        *,
        target: str | None = None,
        safety: str = "standard",
        encoding: str = "P4G_EFIGS",
        library: str = "P4G",
        out_format: str = "V1",
        bit_range_start: int = DEFAULT_MOD_BIT_START,
        bit_range_end: int = DEFAULT_MOD_BIT_END,
        analyzer: Any | None = None,
    ) -> "P4GProject":
        """Create a brand-new script project without manually wrapping Empty(...).

        This is the shortest constructor for users who want to build a new
        standalone script from Python and only need to provide the output target.
        """
        return cls(
            name,
            encoding=encoding,
            library=library,
            out_format=out_format,
            safety=safety,
            source=Empty(target=target),
            bit_range_start=bit_range_start,
            bit_range_end=bit_range_end,
            analyzer=analyzer,
        )

    @classmethod
    def patch_script(
        cls,
        name: str,
        original_bf: str | Path,
        *,
        target: str | None = None,
        import_path: str | None = None,
        copy: bool = True,
        safety: str = "standard",
        encoding: str = "P4G_EFIGS",
        library: str = "P4G",
        out_format: str = "V1",
        bit_range_start: int = DEFAULT_MOD_BIT_START,
        bit_range_end: int = DEFAULT_MOD_BIT_END,
        analyzer: Any | None = None,
    ) -> "P4GProject":
        """Create a patch project without manually wrapping BF(...).

        This is the shortest constructor for hook-based mods that import an
        existing `.bf` file and write a patched replacement.
        """
        return cls(
            name,
            encoding=encoding,
            library=library,
            out_format=out_format,
            safety=safety,
            source=BF(original_bf, import_path=import_path, target=target, copy=copy),
            bit_range_start=bit_range_start,
            bit_range_end=bit_range_end,
            analyzer=analyzer,
        )

    @classmethod
    def new_field_script(
        cls,
        name: str,
        script_name: str,
        *,
        archive: str = "data_e.cpk",
        safety: str = "standard",
        encoding: str = "P4G_EFIGS",
        library: str = "P4G",
        out_format: str = "V1",
        bit_range_start: int = DEFAULT_MOD_BIT_START,
        bit_range_end: int = DEFAULT_MOD_BIT_END,
        analyzer: Any | None = None,
    ) -> "P4GProject":
        """Create a new P4G field-script project with an automatic target path.

        Example:
            P4GProject.new_field_script("night_bonus", "f007")

        The generated project targets `data_e.cpk/field/script/f007.bf` by
        default, which removes a common source of path mistakes for beginners.
        """
        return cls.new_script(
            name,
            target=field_target(script_name, archive=archive),
            safety=safety,
            encoding=encoding,
            library=library,
            out_format=out_format,
            bit_range_start=bit_range_start,
            bit_range_end=bit_range_end,
            analyzer=analyzer,
        )

    @classmethod
    def patch_field_script(
        cls,
        name: str,
        script_name: str,
        original_bf: str | Path,
        *,
        archive: str = "data_e.cpk",
        import_path: str | None = None,
        copy: bool = True,
        safety: str = "standard",
        encoding: str = "P4G_EFIGS",
        library: str = "P4G",
        out_format: str = "V1",
        bit_range_start: int = DEFAULT_MOD_BIT_START,
        bit_range_end: int = DEFAULT_MOD_BIT_END,
        analyzer: Any | None = None,
    ) -> "P4GProject":
        """Create a field-script patch project with an automatic target path.

        This helper keeps the common `f007.bf`-style workflow short: the user
        provides the original file path and the logical script name, while the
        SDK fills the usual `data_e.cpk/field/script/...` target automatically.
        """
        return cls.patch_script(
            name,
            original_bf,
            target=field_target(script_name, archive=archive),
            import_path=import_path,
            copy=copy,
            safety=safety,
            encoding=encoding,
            library=library,
            out_format=out_format,
            bit_range_start=bit_range_start,
            bit_range_end=bit_range_end,
            analyzer=analyzer,
        )

    @classmethod
    def new_event_script(
        cls,
        name: str,
        script_name: str,
        *,
        archive: str = "data_e.cpk",
        safety: str = "standard",
        encoding: str = "P4G_EFIGS",
        library: str = "P4G",
        out_format: str = "V1",
        bit_range_start: int = DEFAULT_MOD_BIT_START,
        bit_range_end: int = DEFAULT_MOD_BIT_END,
        analyzer: Any | None = None,
    ) -> "P4GProject":
        """Create a new P4G event-script project with an automatic target path."""
        return cls.new_script(
            name,
            target=event_target(script_name, archive=archive),
            safety=safety,
            encoding=encoding,
            library=library,
            out_format=out_format,
            bit_range_start=bit_range_start,
            bit_range_end=bit_range_end,
            analyzer=analyzer,
        )

    @classmethod
    def patch_event_script(
        cls,
        name: str,
        script_name: str,
        original_bf: str | Path,
        *,
        archive: str = "data_e.cpk",
        import_path: str | None = None,
        copy: bool = True,
        safety: str = "standard",
        encoding: str = "P4G_EFIGS",
        library: str = "P4G",
        out_format: str = "V1",
        bit_range_start: int = DEFAULT_MOD_BIT_START,
        bit_range_end: int = DEFAULT_MOD_BIT_END,
        analyzer: Any | None = None,
    ) -> "P4GProject":
        """Create an event-script patch project with an automatic target path."""
        return cls.patch_script(
            name,
            original_bf,
            target=event_target(script_name, archive=archive),
            import_path=import_path,
            copy=copy,
            safety=safety,
            encoding=encoding,
            library=library,
            out_format=out_format,
            bit_range_start=bit_range_start,
            bit_range_end=bit_range_end,
            analyzer=analyzer,
        )

    def warn(self, message: str) -> None:
        """Record a warning once so it can be shown in the build manifest."""
        if message not in self.warnings:
            self.warnings.append(message)

    def attach_analyzer(self, analyzer: Any) -> "P4GProject":
        """Attach a decompiled workspace analyzer for conflict-aware builds.

        When an analyzer is attached, reserved bits can move away from values
        already used by the original game scripts, and registered bits can warn
        when they collide with existing scripts.
        """
        self.analyzer = analyzer
        self.resolve_reserved_bits()
        self.validate_registered_bits()
        return self

    def message(self, name: str, *, speaker: Any | None = None, portrait: Any | None = None) -> Message:
        """Create a MessageScript [msg ...] block.

        The returned Message can receive lines with message.line(...). The name
        becomes the symbol used by MSG(name) in generated FlowScript.
        """
        self._ensure_unique(name)
        speaker_text = str(speaker) if speaker is not None else None
        default_bustup = resolve_bustup(portrait if portrait is not None else speaker)
        message = Message(name=name, speaker=speaker_text, default_bustup=default_bustup)
        self.messages.append(message)
        return message

    def selection(self, name: str, *, pattern: str = "top") -> Selection:
        """Create a MessageScript [sel ...] selection block.

        Add options with selection.option(...), then display it from FlowScript
        with proc.sel("choice", selection).
        """
        self._ensure_unique(name)
        selection = Selection(name=name, pattern=pattern)
        self.selections.append(selection)
        return selection

    def procedure(self, name: str, *, return_type: str = "void", params: str = "") -> Procedure:
        """Create a new FlowScript procedure in this project."""
        self._ensure_unique(name, include_messages=False)
        procedure = Procedure(name=name, return_type=return_type, params=params, project=self)
        self.procedures.append(procedure)
        return procedure

    def hook(self, target: str, *, mode: str = "replace", return_type: str = "void", params: str = "") -> Procedure:
        """Create a hook procedure for an existing procedure name.

        Hook modes map to the suffixes expected by AtlusScriptCompiler:
        replace -> _hook, soft/before -> _softhook, after -> _hookafter. Creating
        a hook switches the project to patch mode because it modifies an existing
        .bf script rather than creating a standalone script.
        """
        suffixes = {
            "replace": "_hook",
            "soft": "_softhook",
            "before": "_softhook",
            "after": "_hookafter",
        }
        if mode not in suffixes:
            raise RenderError(f"Unknown hook mode: {mode}")
        # AtlusScriptCompiler truncates FlowScript procedure symbols to 24
        # characters. A 23-character target leaves no room for hook suffixes, so
        # target_hook and target_unhooked can collapse into the same symbol and
        # create broken or recursive compiled code.
        if len(target) > 22:
            raise RenderError(
                f"Hook target name is too long for AtlusScriptCompiler hook suffixes: {target!r}. "
                "Use a target name of 22 characters or fewer; longer names can make "
                "_hook and _unhooked collide after FlowScript symbol truncation."
            )
        self.create_script = False
        return self.procedure(f"{target}{suffixes[mode]}", return_type=return_type, params=params)

    def replace_hook(self, target: str, *, return_type: str = "void", params: str = "") -> Procedure:
        """Create a replace hook for target, rendered as target_hook()."""
        return self.hook(target, mode="replace", return_type=return_type, params=params)

    def soft_hook(self, target: str, *, return_type: str = "void", params: str = "") -> Procedure:
        """Create a soft/before hook for target, rendered as target_softhook()."""
        return self.hook(target, mode="soft", return_type=return_type, params=params)

    def after_hook(self, target: str, *, return_type: str = "void", params: str = "") -> Procedure:
        """Create an after hook for target, rendered as target_hookafter()."""
        return self.hook(target, mode="after", return_type=return_type, params=params)

    def show_message_before_original(
        self,
        target: str,
        speaker_or_message: Any,
        text: str | None = None,
        *,
        condition: Any | None = None,
        mode: str = "replace",
        name: str | None = None,
    ) -> Procedure:
        """Create a hook that shows a message, then calls the original procedure.

        This is the common "add dialogue before vanilla behavior" pattern. Pass
        either an existing Message object or speaker/text, the same way as
        Procedure.say(...). condition can be any condition accepted by proc.if_(...).
        """
        proc = self.hook(target, mode=mode)
        if condition is None:
            proc.say(speaker_or_message, text, name=name)
        else:
            with proc.if_(condition):
                proc.say(speaker_or_message, text, name=name)
        proc.call_original()
        return proc

    def replace_with_message(
        self,
        target: str,
        speaker_or_message: Any,
        text: str | None = None,
        *,
        condition: Any | None = None,
        name: str | None = None,
    ) -> Procedure:
        """Create a replace hook that shows a message instead of original behavior.

        This helper intentionally does not call the original procedure. Use it
        only when the mod should replace that procedure's behavior.
        """
        proc = self.replace_hook(target)
        if condition is None:
            proc.say(speaker_or_message, text, name=name)
        else:
            with proc.if_(condition):
                proc.say(speaker_or_message, text, name=name)
        return proc

    def show_help_once(
        self,
        target: str,
        message_or_text: Any,
        done_bit: BitId | int,
        *,
        condition: Any | None = None,
        mode: str = "replace",
        name: str | None = None,
    ) -> Procedure:
        """Create a hook that displays HELP_MSG once, then calls the original.

        done_bit is checked with BIT_CHK(done_bit) == 0 before the help message
        is shown. After showing the message, the helper sets the bit with
        BIT_ON(done_bit), preventing the help from repeating.
        """
        from .expressions import bitChk

        proc = self.hook(target, mode=mode)
        guard = bitChk(done_bit) == 0
        if condition is None:
            with proc.if_(guard):
                proc.help(message_or_text, name=name)
                proc.setBit(done_bit)
        else:
            with proc.if_(condition):
                with proc.if_(guard):
                    proc.help(message_or_text, name=name)
                    proc.setBit(done_bit)
        proc.call_original()
        return proc

    @property
    def requires_hook(self) -> bool:
        """Return True when this project contains compiler hook procedures."""
        return any(
            procedure.name.endswith(("_hook", "_softhook", "_hookafter"))
            for procedure in self.procedures
        )

    def target(self, path: str) -> "P4GProject":
        """Set the intended in-game output path written to the build manifest."""
        self.target_path = path.replace("\\", "/")
        return self

    def use(
        self,
        source: ScriptSource | str | Path,
        *,
        import_path: str | None = None,
        target: str | None = None,
        copy: bool = True,
    ) -> "P4GProject":
        """Configure this project from BF(...), Empty(...), or a direct path.

        Empty(...) means create mode: no original .bf is imported. BF(...) or a
        direct path means patch mode: the original .bf is imported and can be
        hooked or referenced by generated FlowScript.
        """
        if isinstance(source, ScriptSource):
            if source.empty:
                self.create_script = True
                if source.target_path:
                    self.target(source.target_path)
                return self

            self.create_script = False
            self.import_bf(source.path, import_path=source.import_path, copy=source.copy)
            if source.target_path:
                self.target(source.target_path)
            return self

        source_path = Path(source)
        self.create_script = False
        self.import_bf(source_path, import_path=import_path, copy=copy)
        if target:
            self.target(target)
        return self

    def import_file(
        self,
        source: str | Path,
        *,
        import_path: str | None = None,
        kind: str | None = None,
        copy: bool = True,
    ) -> ProjectImport:
        """Register a file imported by generated FlowScript.

        import_path is the path written into import("..."). When copy=True, the
        builder copies the source file into the build output so the compiler can
        find it next to the generated .flow file.
        """
        source_text = str(source)
        source_path = Path(source_text)
        resolved_import_path = import_path or source_path.name
        resolved_kind = kind or source_path.suffix.lower().lstrip(".") or "file"
        item = ProjectImport(
            source=source_text,
            import_path=resolved_import_path.replace("\\", "/"),
            kind=resolved_kind,
            copy=copy,
        )
        self.imports.append(item)
        return item

    def import_bf(self, source: str | Path, *, import_path: str | None = None, copy: bool = True) -> ProjectImport:
        """Import an original .bf file for patch/hook builds."""
        return self.import_file(source, import_path=import_path, kind="bf", copy=copy)

    def import_flow(self, source: str | Path, *, import_path: str | None = None, copy: bool = True) -> ProjectImport:
        """Import an additional .flow file used by generated FlowScript."""
        return self.import_file(source, import_path=import_path, kind="flow", copy=copy)

    def import_msg(self, source: str | Path, *, import_path: str | None = None, copy: bool = True) -> ProjectImport:
        """Import an additional .msg file used by generated FlowScript."""
        return self.import_file(source, import_path=import_path, kind="msg", copy=copy)

    def const_int(self, name: str, value: int) -> None:
        """Add a top-level FlowScript const int declaration."""
        self.constants.append(f"const int {name} = {value};")

    def reserve_bit(
        self,
        name: str,
        *,
        reason: str | None = None,
        range_start: int | None = None,
        range_end: int | None = None,
        safe: bool = True,
    ) -> BitId:
        """Reserve a named mod bit and return it as a BitId.

        If a workspace analyzer is attached, the SDK tries to avoid bit values
        already used by original scripts. The returned BitId renders as the
        generated const name, so FlowScript stays readable.
        """
        start = self.bit_range_start if range_start is None else range_start
        end = self.bit_range_end if range_end is None else range_end

        if name in self.bit_constants and name not in self.bit_reservations:
            raise DuplicateNameError(f"Bit constant already exists: {name}")

        preferred = self.bit_constants.get(name)
        reserved = {value for key, value in self.bit_constants.items() if key != name}
        value = allocate_bit(
            analyzer=self.analyzer,
            range_start=start,
            range_end=end,
            reserved=reserved,
            preferred=preferred,
        )
        reservation = BitReservation(
            name=name,
            value=value,
            range_start=start,
            range_end=end,
            reason=reason,
            safe=safe,
        )
        self.bit_reservations[name] = reservation
        self.bit_constants[name] = value
        return BitId(value=value, name=name, reason=reason, safe=safe)

    def register_bit(self, bit: BitId) -> None:
        """Register a manually supplied named BitId as a project constant."""
        if bit.name is None:
            return
        if bit.name in self.bit_reservations:
            self.bit_constants[bit.name] = self.bit_reservations[bit.name].value
            return
        existing = self.bit_constants.get(bit.name)
        if existing is not None and existing != bit.value:
            raise DuplicateNameError(f"Bit constant {bit.name} already points to {existing}, not {bit.value}")
        self.bit_constants[bit.name] = bit.value
        if self.analyzer is not None:
            usages = self.analyzer.bit_usages(bit.value)
            if usages:
                self.warn(f"Bit {bit.name}={bit.value} appears in original scripts {len(usages)} time(s)")

    def resolve_reserved_bits(self) -> None:
        """Move reserved bits away from known workspace collisions when possible."""
        if not self.bit_reservations:
            return

        reserved_values = {value for name, value in self.bit_constants.items() if name not in self.bit_reservations}
        for name, reservation in list(self.bit_reservations.items()):
            value = allocate_bit(
                analyzer=self.analyzer,
                range_start=reservation.range_start,
                range_end=reservation.range_end,
                reserved=reserved_values,
                preferred=reservation.value,
            )
            if value != reservation.value:
                self.warn(f"Reserved bit {name} moved from {reservation.value} to {value} because the previous value is occupied")
            updated = BitReservation(
                name=name,
                value=value,
                range_start=reservation.range_start,
                range_end=reservation.range_end,
                reason=reservation.reason,
                safe=reservation.safe,
            )
            self.bit_reservations[name] = updated
            self.bit_constants[name] = value
            reserved_values.add(value)

    def validate_registered_bits(self) -> None:
        """Warn when manually registered bits are already used by original scripts."""
        if self.analyzer is None:
            return
        for name, value in sorted(self.bit_constants.items()):
            usages = self.analyzer.bit_usages(value)
            if usages:
                self.warn(f"Bit {name}={value} appears in original scripts {len(usages)} time(s)")

    def render_msg(self) -> str:
        """Render all project messages and selections as a .msg document."""
        return MessageDocument(messages=self.messages, selections=self.selections).render()

    def render_flow(self) -> str:
        """Render all imports, constants, and procedures as a .flow document."""
        if not self.procedures:
            raise RenderError("Project has no procedures")
        imports = [item.import_path for item in self.imports]
        if self.messages or self.selections:
            imports.append(f"{self.name}.msg")
        bit_constants = [f"const int {name} = {value};" for name, value in sorted(self.bit_constants.items())]
        constants = bit_constants + self.constants
        return FlowDocument(imports=imports, constants=constants, procedures=self.procedures).render()

    def write(self, out_dir: str | Path) -> tuple[Path, Path | None]:
        """Write generated .flow and .msg source files into out_dir."""
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        flow_path = out_path / f"{self.name}.flow"
        flow_path.write_text(self.render_flow(), encoding="utf-8")

        msg_path: Path | None = None
        if self.messages or self.selections:
            msg_path = out_path / f"{self.name}.msg"
            msg_path.write_text(self.render_msg(), encoding="utf-8")

        return flow_path, msg_path

    def compile(
        self,
        out_dir: str | Path,
        *,
        compiler_path: str | Path | None = None,
        hook: bool | None = None,
        debug: bool = False,
    ) -> CompileResult:
        """Compile this project into a .bf file with AtlusScriptCompiler.

        The method writes fresh .flow/.msg sources first, then invokes the
        compiler. debug=True prints the compiler command and compiler output.
        """
        flow_path, _ = self.write(out_dir)
        output_bf = Path(out_dir) / f"{self.name}.bf"
        config = CompilerConfig(
            compiler_path=compiler_path,
            library=self.library,
            encoding=self.encoding,
            out_format=self.out_format,
            hook=self.requires_hook if hook is None else hook,
            debug=debug,
        )
        return compile_flow(flow_path, output_bf, config)

    def build(
        self,
        out_dir: str | Path | None = None,
        *,
        compile_bf: bool = True,
        compiler_path: str | Path | None = None,
        hook: bool | None = None,
        workspace: str | Path | Any | None = None,
        safety: str | None = None,
        allow_conflicts: bool = False,
        package_out: str | Path | None = None,
        debug: bool = False,
    ) -> "BuildResult":
        """Build this project and return a BuildResult.

        Build writes .flow/.msg, optionally compiles .bf, writes manifests, runs
        conflict checks when workspace is provided, and can package the resulting
        .bf into an install directory.
        """
        from .builder import build_project

        resolved_out_dir = Path(out_dir) if out_dir is not None else (Path.cwd() / "build" / self.name)
        return build_project(
            self,
            resolved_out_dir,
            compile_bf=compile_bf,
            compiler_path=compiler_path,
            hook=hook,
            workspace=workspace,
            safety=safety,
            allow_conflicts=allow_conflicts,
            package_out=package_out,
            debug=debug,
        )

    def Build(
        self,
        out_dir: str | Path | None = None,
        *,
        compile_bf: bool = True,
        compiler_path: str | Path | None = None,
        hook: bool | None = None,
        workspace: str | Path | Any | None = None,
        safety: str | None = None,
        allow_conflicts: bool = False,
        package_out: str | Path | None = None,
        Debug: bool = False,
        debug: bool | None = None,
    ) -> "BuildResult":
        """Beginner-friendly alias for build(...).

        Debug is accepted with a capital D because examples often present the
        user-facing API this way. Passing debug=... also works and overrides
        Debug when both are provided.
        """
        return self.build(
            out_dir,
            compile_bf=compile_bf,
            compiler_path=compiler_path,
            hook=hook,
            workspace=workspace,
            safety=safety,
            allow_conflicts=allow_conflicts,
            package_out=package_out,
            debug=Debug if debug is None else debug,
        )

    def _ensure_unique(self, name: str, *, include_messages: bool = True) -> None:
        names: set[str] = set()
        if include_messages:
            names.update(message.name for message in self.messages)
            names.update(selection.name for selection in self.selections)
        names.update(procedure.name for procedure in self.procedures)
        if name in names:
            raise DuplicateNameError(f"Name already exists: {name}")



