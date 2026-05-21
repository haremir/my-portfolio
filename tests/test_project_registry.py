import unittest

from harun_site.utils.data_manager import load_projects
from harun_site.utils.project_registry import resolve_project


class ProjectRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projects = load_projects()

    def assert_resolves_to_cebirx(self, query: str) -> None:
        project = resolve_project(query, self.projects)
        self.assertIsNotNone(project)
        self.assertEqual(project["id"], "cebirx")
        self.assertEqual(project["title"], "CebirX")
        self.assertEqual(project["slug"], "cebirx")
        self.assertEqual(project["url"], "/portfolio/cebirx")

    def test_resolve_cebrix(self):
        self.assert_resolves_to_cebirx("cebrix")

    def test_resolve_cebix(self):
        self.assert_resolves_to_cebirx("cebix")

    def test_resolve_cebr_x(self):
        self.assert_resolves_to_cebirx("cebr x")

    def test_resolve_cebir_dash_x(self):
        self.assert_resolves_to_cebirx("cebir-x")

    def test_unresolved_query_returns_none(self):
        self.assertIsNone(resolve_project("completely unrelated", self.projects))


if __name__ == "__main__":
    unittest.main()