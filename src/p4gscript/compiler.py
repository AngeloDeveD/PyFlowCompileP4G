from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess

from .exceptions import CompilerError


@dataclass(frozen=True)
class CompilerConfig:
    compiler_path: str | Path | None = None
    library: str = "P4G"
    encoding: str = "P4G_EFIGS"
    out_format: str = "V1"
    hook: bool = False
    debug: bool = False


@dataclass(frozen=True)
class CompileResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def bundled_compiler_root() -> Path:
    return Path(__file__).resolve().parents[2] / "tools" / "AtlusScriptTools"


def bundled_compiler_path() -> Path:
    return bundled_compiler_root() / "AtlusScriptCompiler.exe"


def resolve_compiler_path(compiler_path: str | Path | None = None) -> Path:
    candidates: list[Path | str] = []
    if compiler_path is not None:
        candidates.append(compiler_path)

    env_compiler = os.environ.get("P4GSCRIPT_COMPILER")
    if env_compiler:
        candidates.append(env_compiler)

    candidates.append(bundled_compiler_path())
    candidates.append(Path(__file__).resolve().parents[3] / "Build" / "Release" / "net8.0" / "AtlusScriptCompiler.exe")
    candidates.extend(["AtlusScriptCompiler.exe", "AtlusScriptCompiler"])

    for candidate in candidates:
        resolved = _resolve_candidate(candidate)
        if resolved is not None:
            return resolved

    raise CompilerError(
        "AtlusScriptCompiler was not found. "
        "Bundle it into tools/AtlusScriptTools, "
        "set P4GSCRIPT_COMPILER, or pass compiler_path explicitly."
    )


def compile_flow(input_flow: str | Path, output_bf: str | Path, config: CompilerConfig) -> CompileResult:
    compiler = resolve_compiler_path(config.compiler_path)
    input_flow_path = Path(input_flow).resolve()
    output_bf_path = Path(output_bf).resolve()
    command = [
        str(compiler),
        "-Compile",
        "-In",
        str(input_flow_path),
        "-Out",
        str(output_bf_path),
        "-Library",
        config.library,
        "-Encoding",
        config.encoding,
        "-OutFormat",
        config.out_format,
    ]
    if config.hook:
        command.insert(2, "-Hook")

    completed = subprocess.run(
        command,
        capture_output=True,
        check=False,
        cwd=str(compiler.parent),
    )
    result = CompileResult(
        command=command,
        returncode=completed.returncode,
        stdout=_decode_output(completed.stdout),
        stderr=_decode_output(completed.stderr),
    )
    if config.debug:
        print("AtlusScriptCompiler command:")
        print("  " + " ".join(command))
        if result.stdout:
            print("AtlusScriptCompiler stdout:")
            print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
        if result.stderr:
            print("AtlusScriptCompiler stderr:")
            print(result.stderr, end="" if result.stderr.endswith("\n") else "\n")
    if result.returncode != 0:
        raise CompilerError(result.stderr or result.stdout or "AtlusScriptCompiler failed")
    return result



def _decode_output(data: bytes | str | None) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        return _normalize_output(data.replace("\x00", ""))
    if not data:
        return ""

    for encoding in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            decoded = data.decode(encoding)
        except UnicodeDecodeError:
            continue
        if decoded.count("\x00") <= max(1, len(decoded) // 20):
            return _normalize_output(decoded.replace("\x00", ""))

    return _normalize_output(data.decode("utf-8", errors="replace").replace("\x00", ""))


def _normalize_output(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")

def _resolve_candidate(candidate: Path | str) -> Path | None:
    if isinstance(candidate, Path):
        path = candidate
    else:
        path = Path(candidate)

    if path.exists():
        if path.is_dir():
            nested = path / "AtlusScriptCompiler.exe"
            if nested.exists():
                return nested.resolve()
        if path.is_file():
            return path.resolve()

    resolved = shutil.which(str(candidate))
    if resolved:
        return Path(resolved).resolve()
    return None





