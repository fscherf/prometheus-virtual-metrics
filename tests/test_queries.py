from prometheus_virtual_metrics.promql import PromqlQuery


def test_names():

    # name
    query = PromqlQuery('foo')

    assert query.name_matches(name="foo")
    assert query.matches(name="foo")

    assert not query.name_matches(name="bar")
    assert not query.matches(name="bar")

    # __name__: equal
    query = PromqlQuery('{__name__="foo"}')

    assert query.name_matches(name="foo")
    assert query.matches(name="foo")

    assert not query.name_matches(name="bar")
    assert not query.matches(name="bar")

    # __name__: not equal
    # we need at least one non-empty matcher for a valid query
    query = PromqlQuery('{__name__!="foo",a="b"}')

    assert not query.name_matches(name="foo")
    assert not query.matches(name="foo", labels={'a': 'b'})

    assert query.name_matches(name="bar")
    assert query.matches(name="bar", labels={'a': 'b'})

    # __name__: regex
    query = PromqlQuery('{__name__=~"foo|bar"}')

    assert query.name_matches(name="foo")
    assert query.name_matches(name="bar")
    assert query.matches(name="foo")
    assert query.matches(name="bar")

    assert not query.name_matches(name="baz")
    assert not query.matches(name="baz")

    # __name__: not regex
    # we need at least one non-empty matcher for a valid query
    query = PromqlQuery('{__name__!~"foo|bar",a="b"}')

    assert not query.name_matches(name='foo')
    assert not query.name_matches(name='bar')
    assert not query.matches(name="foo", labels={'a': 'b'})
    assert not query.matches(name="bar", labels={'a': 'b'})

    assert query.name_matches(name='baz')
    assert query.matches(name="baz", labels={'a': 'b'})


def test_labels():

    # equal
    query = PromqlQuery('{foo="bar"}')

    assert query.matches(labels={"foo": "bar"})
    assert not query.matches(labels={"foo": "baz"})

    # not equal
    # we need at least one non-empty matcher for a valid query
    query = PromqlQuery('{foo!="bar",a="b"}')

    assert not query.matches(labels={"foo": "bar", 'a': 'b'})
    assert query.matches(labels={"foo": "baz", 'a': 'b'})

    # regex
    query = PromqlQuery('{foo=~"foo|bar"}')

    assert query.matches(labels={'foo': 'foo'})
    assert query.matches(labels={'foo': 'bar'})
    assert not query.matches(labels={'foo': 'baz'})

    # not regex
    # we need at least one non-empty matcher for a valid query
    query = PromqlQuery('{foo!~"foo|bar",a="b"}')

    assert not query.matches(labels={'foo': 'foo', 'a': 'b'})
    assert not query.matches(labels={'foo': 'bar', 'a': 'b'})
    assert query.matches(labels={'foo': 'baz', 'a': 'b'})


def test_combinations():

    # with name, with label
    query = PromqlQuery('foo{bar="baz"}')

    assert query.name_matches('foo')
    assert not query.name_matches('bar')

    assert query.matches(name='foo', labels={'bar': 'baz'})
    assert not query.matches(name='bar', labels={'bar': 'baz'})
    assert not query.matches(name='foo', labels={'baz': 'bar'})

    # without name, with label
    query = PromqlQuery('{foo="bar"}')

    assert query.name_matches('name1')
    assert query.name_matches('name2')

    assert query.matches(name='name1', labels={'foo': 'bar'})
    assert query.matches(name='name2', labels={'foo': 'bar'})
    assert query.matches(labels={'foo': 'bar'})

    assert not query.matches(name='name1', labels={'bar': 'foo'})
    assert not query.matches(name='name2', labels={'bar': 'foo'})
    assert not query.matches(labels={'bar': 'foo'})

    # name as regex
    query = PromqlQuery('{__name__=~"foo|bar"}')

    assert query.name_matches('foo')
    assert query.name_matches('bar')
    assert not query.name_matches('baz')

    assert query.matches(name='foo')
    assert query.matches(name='foo', labels={'foo': 'bar'})
    assert query.matches(name='bar')
    assert query.matches(name='bar', labels={'foo': 'bar'})
    assert not query.matches(name='baz')
    assert not query.matches(name='baz', labels={'foo': 'bar'})
