"""Ports and error vocabulary the corpus harness depends on.

The harness has exactly one port: the domain compares outcomes, and only the
way an implementation is started varies between the test suite, a future pokie
runner (roadmap task 2.1.3), and a unit test's stand-in.
"""

import typing as typ

if typ.TYPE_CHECKING:
    import pathlib

    from job_corpus import model


class EvidenceFormatError(Exception):
    """Raised when the corpus cannot express what the harness needs.

    The error is a defect in the evidence, not a result of the program under
    test: a malformed job file, a script that does not exist, or an
    implementation kind nothing can run yet.

    Attributes
    ----------
    path : pathlib.PurePosixPath
        The corpus-relative document the problem is in.
    key : str
        The dotted TOML key, or an equivalent location, in that document.
    """

    def __init__(self, message: str, *, path: pathlib.PurePosixPath, key: str) -> None:
        """Record where the defect is, so every report names it.

        Parameters
        ----------
        message : str
            The diagnostic, without its location.
        path : pathlib.PurePosixPath
            The corpus-relative document the problem is in.
        key : str
            The dotted TOML key, or an equivalent location, in that document.
        """
        formatted = f"{path}: {key}: {message}"
        super().__init__(formatted)
        self.path = path
        self.key = key


class ProgramRunner(typ.Protocol):
    """Runs one implementation of one case and reports what it did.

    A runner reports bytes, status, and timeouts; `job_corpus.comparison` judges
    them.
    """

    def run(
        self, implementation: model.ScriptImplementation, case: model.JobCase
    ) -> model.ObservedOutcome:
        """Run one implementation over one case.

        Parameters
        ----------
        implementation : model.ScriptImplementation
            The script to run, with its fixed arguments and comparison mode.
        case : model.JobCase
            The case whose inputs and operands the run uses.

        Returns
        -------
        model.ObservedOutcome

        Raises
        ------
        EvidenceFormatError
            If the corpus cannot express this run, for example because the
            script file is missing.
        """
