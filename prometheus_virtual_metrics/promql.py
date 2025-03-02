import re

import promql_parser


class PromqlQuery:
    """
    Attributes:
        string (str): PromQL query as string
        ast (promql_parser.Ast | None): PromQL query object
        name (str): Requested metric name in `ast`
    """

    def __init__(self, query_string):
        self.string = query_string

        self.ast = None
        self.name = ''

        # parse query string
        if self.string:
            self.ast = promql_parser.parse(self.string)

            # find metric name
            # vector selector: foo{bar="baz"}
            if isinstance(self.ast, promql_parser.VectorSelector):
                self.name = self.ast.name

            # matrix selector: foo{bar="baz"}[5m]
            elif isinstance(self.ast, promql_parser.MatrixSelector):
                self.name = self.ast.vector_selector.name

            # aggregate expression: sum(foo{bar="baz"})
            elif isinstance(self.ast, promql_parser.AggregateExpr):
                self.name = self.ast.expr.name

    def __repr__(self):
        return f'<PromqlQuery({self.string!r})>'

    def _apply_matcher(self, matcher, value):

        # equal (=)
        if (matcher.op == promql_parser.MatchOp.Equal and
                matcher.value == value):

            return True

        # not equal (!=)
        elif (matcher.op == promql_parser.MatchOp.NotEqual and
                matcher.value != value):

            return True

        # regex (=~)
        elif (matcher.op == promql_parser.MatchOp.Re and
                re.fullmatch(matcher.value, value)):

            return True

        # not regex (!~)
        elif (matcher.op == promql_parser.MatchOp.NotRe and
                not re.fullmatch(matcher.value, value)):

            return True

        return False

    def name_matches(self, name):
        """
        Returns `True` when the given string matches `query`

        Args:
            name (str): Metric name

        Returns:
            (bool): Given string matches `query`
        """

        # everything matches an empty query
        if not self.ast:
            return True

        # name
        if self.name:
            return self.name == name

        # __name__
        for matcher in self.ast.matchers.matchers:
            if matcher.name != '__name__':
                continue

            return self._apply_matcher(
                matcher=matcher,
                value=name,
            )

        # no name was queried
        return True

    def matches(self, name='', labels=None):
        """
        Returns `True` when the given string and labels match `query`

        Args:
            name (str): Metric name
            labels (dict[str,str] | None): Metric labels

        Returns:
            (bool): Given string and labels match `query`
        """

        # everything matches an empty query
        if not self.ast:
            return True

        # name
        if not self.name_matches(name):
            return False

        # labels
        labels = labels or {}

        for matcher in self.ast.matchers.matchers:
            if matcher.name == '__name__':
                continue

            value = labels.get(matcher.name, '')

            if not self._apply_matcher(matcher=matcher, value=value):
                return False

        return True
