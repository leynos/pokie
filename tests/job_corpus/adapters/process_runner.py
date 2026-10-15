r"""Run corpus implementations as child processes.

The runner is the only place in the harness that starts another program. It
always passes an argument list, never a shell, and always gives the child an
explicit environment allowlist: an inherited environment would make a case's
outcome depend on the developer's locale, search path, or Python
configuration.

Materializing a case's inputs and building that environment are module-level
functions because neither needs the runner: only the command shape and the
time limit vary between runs.
"""

import dataclasses
import os
import pathlib
import subprocess  # ruff: ignore[suspicious-subprocess-import] - the harness runs corpus implementations and nothing else.
import sys
import tempfile

from job_corpus import model
from job_corpus.ports import EvidenceFormatError

_TIMEOUT_STATUS = -1


def _materialize(
    case: model.JobCase, directory: pathlib.Path
) -> tuple[list[str], bytes]:
    """Write the case's inputs and resolve its operands.

    A lone ``-`` operand keeps standard input, so a stdin case stays
    testable; every other operand becomes the path of the file just
    written. Inputs exist only for the duration of the run.

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
        If an operand names no input in the case.
    """
    by_name = {input_file.name: input_file for input_file in case.inputs}
    resolved: list[str] = []
    for operand in case.operands:
        if operand == "-":
            resolved.append(operand)
            continue
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
    if resolved == ["-"] and case.inputs:
        return resolved, case.inputs[0].content
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
            reported outcome, not an exception, so one slow implementation
            cannot abort the whole corpus run.
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
