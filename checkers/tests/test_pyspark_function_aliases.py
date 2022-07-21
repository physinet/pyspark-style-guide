import pyspark_function_aliases
import pylint.testutils
import astroid


class TestPySparkFunctionAliasChecker(pylint.testutils.CheckerTestCase):
    CHECKER_CLASS = pyspark_function_aliases.PySparkFunctionAliasChecker

    def test_finds_non_unique_ints(self):
        nodes = astroid.extract_node(
            """
        def test(df):
            df.filter()  #@
            df.groupBy()  #@
            df.where()  #@
            df.groupby()  #@
        """
        )

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(
                msg_id=pyspark_function_aliases.NAME,
                line=3,
                node=nodes[0],
                col_offset=4,
                end_line=3,
                end_col_offset=15,
            )
        ):
            self.checker.visit_call(nodes[0])

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(
                msg_id=pyspark_function_aliases.NAME,
                line=4,
                node=nodes[1],
                col_offset=4,
                end_line=4,
                end_col_offset=16,
            )
        ):
            self.checker.visit_call(nodes[1])

        with self.assertNoMessages():
            for node in nodes[2:]:
                self.checker.visit_call(node)
