# built-in
from pathlib import Path
from random import shuffle

# external
import pytest
from dephell_discover import Data, Package
from dephell_links import VCSLink

# project
from dephell.converters.setuppy import SetupPyConverter
from dephell.models import Requirement


def test_load_deps():
    path = Path('tests') / 'requirements' / 'setup.py'
    root = SetupPyConverter().load(path)

    needed = {'attrs', 'cached-property', 'packaging', 'requests', 'colorama', 'libtest'}
    assert {dep.name for dep in root.dependencies} == needed


def test_load_metadata():
    path = Path('tests') / 'requirements' / 'setup.py'
    root = SetupPyConverter().load(path)

    assert root.name == 'dephell'
    assert root.version == '0.2.0'
    assert root.authors[0].name == 'orsinium'
    assert len(root.classifiers) == 4
    assert len(root.keywords) == 3
    assert not root.license


def test_dumps_deps():
    path = Path('tests') / 'requirements' / 'setup.py'
    converter = SetupPyConverter()
    resolver = converter.load_resolver(path)
    reqs = Requirement.from_graph(graph=resolver.graph, lock=False)
    assert len(reqs) > 2

    content = converter.dumps(reqs=reqs, project=resolver.graph.metainfo)
    print(content)
    root = SetupPyConverter().loads(content)
    needed = {'attrs', 'cached-property', 'packaging', 'requests', 'colorama', 'libtest'}
    assert {dep.name for dep in root.dependencies} == needed


def test_dependency_links_load():
    content = """
        __import__("setuptools").setup(
            name="lol",
            version="0.1.0",
            install_requires=["libtest"],
            dependency_links=["git+https://github.com/gwtwod/poetrylibtest#egg=libtest-0.1.0"],
        )
    """
    converter = SetupPyConverter()
    resolver = converter.loads_resolver(content.strip())
    reqs = Requirement.from_graph(graph=resolver.graph, lock=False)
    reqs = {req.name: req for req in reqs}
    assert type(reqs['libtest'].link) is VCSLink


@pytest.mark.parametrize('number_of_runs', range(5))
def test_package_data_is_sorted_across_runs(number_of_runs):
    path = Path('tests') / 'requirements' / 'setup.py'
    converter = SetupPyConverter()
    resolver = converter.load_resolver(path)
    package_paths = [
        ('./a/b', './a/b', 'project.a.b'),
        ('./b', './b', 'project.b'),
        ('./m/z', './m', 'project.m'),
        ('./a/z', './a/z', 'project.a.z'),
        ('./x/a', './x/a', 'project.x.a'),
        ('./n/a', './n/a', 'project.n.a'),
        ('./x/n', './x/n', 'project.x.n'),
        ('./b/c', './b/c', 'project.b.c'),
    ]
    package_data_sorted = """
    package_data={
        'project.a.b': ['*.txt'],
        'project.a.z': ['*.txt'],
        'project.b': ['*.txt'],
        'project.b.c': ['*.txt'],
        'project.m': ['z/*.txt'],
        'project.n.a': ['*.txt'],
        'project.x.a': ['*.txt'],
        'project.x.n': ['*.txt']
    """
    # Make order of paths random at each test run
    shuffle(package_paths)
    package_data = {
        Data(
            path=Path(path[0]),
            ext='.txt',
            package=Package(
                path=Path(path[1]),
                root=Path('.'),
                module=path[2],
            ),
        ) for path in package_paths
    }
    root = converter.load(path)
    root.package.data = package_data
    reqs = Requirement.from_graph(graph=resolver.graph, lock=False)
    content_package_data = converter.dumps(reqs=reqs, project=root)
    assert package_data_sorted.strip() in content_package_data
