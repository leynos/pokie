r"""Run corpus implementations as child processes.

The runner and `awk_version` are the only places in the harness that start
another program. They pass an argument list, never a shell, and an explicit
environment allowlist, so no outcome depends on the developer's locale.

Materializing a case's inputs and building that environment need no runner, so
both are module-level: only the command shape and time limit vary per run.
"""

import dataclasses
import os
import pathlib
import subprocess  # ruff: ignore[suspicious-subprocess-import] - the harness runs corpus implementations and the host awk probe, and nothing else.
import sys
import tempfile
import typing as typ

from job_corpus import model
from job_corpus.ports import EvidenceFormatError

if typ.TYPE_CHECKING:
    import collections.abc as cabc

_TIMEOUT_STATUS = -1

_PROBE_FAILURES = (OSError, subprocess.SubprocessError)
"""What a missing or misbehaving awk raises, and what the probe must survive.

Named rather than written inline because the repository's lint runs one parser
that predates unparenthesized ``except`` tuples.
"""


def _inputs_by_name(case: model.JobCase) -> dict[str, model.InputFile]:
    """Return the case's inputs keyed by name, refusing any ambiguity.

    Every input name must be a bare file name and no two may coincide: the name
    maps an operand to bytes, so a path-like or reused name reads other bytes.

    Parameters
    ----------
    case : model.JobCase
        The case whose inputs the lookup is built from.

    Returns
    -------
    dict[str, model.InputFile]
        The inputs keyed by name.

    Raises
    ------
    EvidenceFormatError
        If a name is not a bare file name, or two inputs share one.
    """
    by_name: dict[str, model.InputFile] = {}
    for input_file in case.inputs:
        name = pathlib.PurePosixPath(input_file.name)
        if name.name != input_file.name or name.name in {"", ".", ".."}:
            message = (
                f"the input name {input_file.name!r} is not a bare file name; "
                "an operand can only select a file directly inside the run "
                "directory"
            )
            raise EvidenceFormatError(
                message,
                path=pathlib.PurePosixPath(case.case_id),
                key="inputs",
            )
        if input_file.name in by_name:
            message = (
                f"the case lists two inputs named {input_file.name!r}, "
                "so its operands could not say which one they mean"
            )
            raise EvidenceFormatError(
                message,
                path=pathlib.PurePosixPath(case.case_id),
                key="inputs",
            )
        by_name[input_file.name] = input_file
    return by_name


def _materialize(
    case: model.JobCase, directory: pathlib.Path
) -> tuple[list[str], bytes]:
    """Write the case's inputs and resolve its operands.

    An absent operand, or a lone ``-``, reads standard input and so needs
    exactly one input: the runner cannot know which of several a program would
    read. Every other operand names a file written for the run alone.

    Parameters
    ----------
    case : model.JobCase
        The case whose inputs and operands the run uses.
    directory : pathlib.Path
        The temporary directory the inputs are written into.

    Returns
    -------
    tuple[list[str], bytes]
        The resolved operands and the bytes for standard input.

    Raises
    ------
    EvidenceFormatError
        If an operand names no input in the case, the case reads standard
        input without exactly one input to feed it, or its input names are not
        usable as operands (see `_inputs_by_name`).
    """
    by_name = _inputs_by_name(case)
    if not case.operands or case.operands == ("-",):
        if len(case.inputs) != 1:
            message = (
                "standard input needs exactly one input to feed it, "
                f"but the case lists {len(case.inputs)}"
            )
            raise EvidenceFormatError(
                message,
                path=pathlib.PurePosixPath(case.case_id),
                key="inputs",
            )
        return list(case.operands), case.inputs[0].content
    if "-" in case.operands:
        message = (
            "'-' cannot be combined with file operands, because the case "
            "cannot say which input it would read"
        )
        raise EvidenceFormatError(
            message,
            path=pathlib.PurePosixPath(case.case_id),
            key="operands",
        )
    resolved: list[str] = []
    for operand in case.operands:
        if operand not in by_name:
            message = f"the case lists no input named {operand!r}"
            raise EvidenceFormatError(
                message,
                path=pathlib.PurePosixPath(case.case_id),
                key="operands",
            )
        target = directory / operand
        target.write_bytes(by_name[operand].content)
        resolved.append(str(target))
    return resolved, b""


def _environment(kind: model.ScriptKind) -> dict[str, str]:
    """Return the child's environment allowlist for one implementation kind.

    Parameters
    ----------
    kind : model.ScriptKind
        The implementation kind being run.

    Returns
    -------
    dict[str, str]
        The environment the child receives; no other inherited key is
        passed, so a stray ``PYTHONPATH`` cannot reach the oracle.
    """
    locale = "C.UTF-8" if kind is model.ScriptKind.REFERENCE else "C"
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LC_ALL": locale}


def awk_version(
    executable: str,
    *,
    run: cabc.Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    """Return the first version line ``executable`` prints, or ``""``.

    Both spellings are tried because mawk and gawk answer ``-W version`` and
    other awks only ``--version``. Standard input is closed so an awk that
    treats ``version`` as program text cannot block, the environment is the
    module's allowlist so no banner depends on the caller's locale, and any
    failure returns ``""`` rather than raising: a host without a probe is
    reported, never fatal.

    Parameters
    ----------
    executable : str
        The resolved awk to probe.
    run : cabc.Callable[..., subprocess.CompletedProcess[str]]
        The process launcher, injectable so every outcome is testable.

    Returns
    -------
    str
        The banner's first line, or ``""`` when no probe yields one.
    """
    for arguments in (("-W", "version"), ("--version",)):
        try:
            completed = run(
                [executable, *arguments],
                capture_output=True,
                stdin=subprocess.DEVNULL,
                text=True,
                timeout=10,
                check=False,
                env=_environment(model.ScriptKind.AWK),
            )
        except _PROBE_FAILURES:
            continue
        banner = (completed.stdout + completed.stderr).strip()
        if completed.returncode == 0 and banner:
            return banner.splitlines()[0].strip()
    return ""


@dataclasses.dataclass(frozen=True, slots=True)
class ProcessRunner:
    """Run an implementation with a fixed command shape per script kind.

    The reference runs under ``sys.executable -I`` so that no user site
    directory, ``PYTHON*`` variable, or checkout-relative module can change
    what the oracle does. The awk and shell alternatives run under ``LC_ALL=C``
    because their output comparison depends on byte order.

    Attributes
    ----------
    corpus_root : pathlib.Path
        Directory the implementation paths are relative to.
    awk_executable : str | None
        The awk on this host, or ``None`` when none is installed. ``None``
        makes an awk run fail as unsupported rather than quietly succeed.
    timeout : float
        Seconds before a run is reported as timed out rather than finished.
    """

    corpus_root: pathlib.Path
    awk_executable: str | None = None
    timeout: float = 10.0

    def run(
        self, implementation: model.ScriptImplementation, case: model.JobCase
    ) -> model.ObservedOutcome:
        r"""Run one implementation over one case.

        For example, a reference script that prints ``1 2`` and exits zero is
        reported as ``ObservedOutcome(b"1 2\n", b"", 0, False)``.

        Parameters
        ----------
        implementation : model.ScriptImplementation
            The script to run.
        case : model.JobCase
            The case whose inputs and operands the run uses.

        Returns
        -------
        model.ObservedOutcome
            The captured bytes, exit status, and timeout flag.

        Raises
        ------
        EvidenceFormatError
            If the script is missing from the corpus, an operand names no
            input, or the implementation kind cannot be run here.
        """
        script = self.corpus_root / implementation.path
        if not script.is_file():
            message = "the corpus names no such script; add it or correct the path"
            raise EvidenceFormatError(
                message,
                path=implementation.path,
                key="path",
            )
        with tempfile.TemporaryDirectory(prefix="job-corpus-") as directory:
            operands, standard_input = _materialize(case, pathlib.Path(directory))
            command = self._command(implementation, script, operands)
            return self._execute(command, standard_input, implementation.kind)

    def _execute(
        self, command: list[str], standard_input: bytes, kind: model.ScriptKind
    ) -> model.ObservedOutcome:
        """Run the command and turn its result into an observed outcome.

        Parameters
        ----------
        command : list[str]
            The complete argument list.
        standard_input : bytes
            Bytes to feed the child, empty when it reads named files.
        kind : model.ScriptKind
            The implementation kind, which selects the environment.

        Returns
        -------
        model.ObservedOutcome
            The captured bytes, exit status, and timeout flag. A timeout is a
            reported outcome, so one slow implementation aborts no run.
        """
        try:
            completed = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - argument list, no shell.
                command,
                input=standard_input,
                capture_output=True,
                check=False,
                timeout=self.timeout,
                env=_environment(kind),
            )
        except subprocess.TimeoutExpired:
            return model.ObservedOutcome(
                stdout=b"", stderr=b"", exit_status=_TIMEOUT_STATUS, timed_out=True
            )
        return model.ObservedOutcome(
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_status=completed.returncode,
        )

    def _command(
        self,
        implementation: model.ScriptImplementation,
        script: pathlib.Path,
        operands: list[str],
    ) -> list[str]:
        """Build the argument list for one implementation kind.

        Parameters
        ----------
        implementation : model.ScriptImplementation
            The script to run.
        script : pathlib.Path
            The script's absolute path.
        operands : list[str]
            The case's resolved operands.

        Returns
        -------
        list[str]
            The complete argument list.

        Raises
        ------
        EvidenceFormatError
            If the kind cannot be run on this host.
        """
        match implementation.kind:
            case model.ScriptKind.REFERENCE:
                head = [sys.executable, "-I", str(script)]
            case model.ScriptKind.AWK:
                head = [self._require_awk(), "-f", str(script)]
            case model.ScriptKind.SHELL:
                head = ["sh", str(script)]
            case _:
                message = f"nothing runs a {implementation.kind} implementation here"
                raise EvidenceFormatError(
                    message,
                    path=implementation.path,
                    key="kind",
                )
        return [*head, *implementation.args, *operands]

    def _require_awk(self) -> str:
        """Return the awk executable, refusing to run when none is installed.

        Returns
        -------
        str
            The awk executable's name or path.

        Raises
        ------
        EvidenceFormatError
            If this host has no awk, so the shortfall is reported rather than
            counted as agreement.
        """
        if self.awk_executable is None:
            message = "no awk is installed on this host, so the alternative cannot run"
            raise EvidenceFormatError(
                message,
                path=pathlib.PurePosixPath("jobs"),
                key="awk",
            )
        return self.awk_executable
