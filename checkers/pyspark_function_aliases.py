import astroid
from astroid import nodes
from typing import TYPE_CHECKING, Optional

from pylint.checkers import BaseChecker

if TYPE_CHECKING:
    from pylint.lint import PyLinter


def register(linter: "PyLinter") -> None:
    """This required method auto registers the checker during initialization.
    :param linter: The linter to register the checker to.
    """
    linter.register_checker(PySparkFunctionAliasChecker(linter))


NAME = "pyspark-less-desirable-function-alias"
ALIASES = {
    "filter": "where",
    "groupBy": "groupby",
    "dropDuplicates": "drop_duplicates",
    "cast": "astype",
    "name": "alias",
    "avg": "mean",
    "stddev_sample": "stddev",
    "var_sample": "var",
}


class PySparkFunctionAliasChecker(BaseChecker):

    name = "pyspark-function-alias"
    msgs = {
        "C3901": (
            "Calls a less desirable alias for a common PySpark function.",
            NAME,
            "PySpark functions should use the most Pythonic, specific, and concise names when other aliases exist.",
        ),
    }

    def __init__(self, linter: Optional["PyLinter"] = None) -> None:
        super().__init__(linter)
        self._function_stack = []

    def visit_call(self, node: nodes.Call) -> None:
        if node.func.attrname in ALIASES:
            self.add_message(NAME, node=node)
