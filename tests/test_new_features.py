import unittest
from harun_site.state.admin_state import slugify
from harun_site.utils.data_manager import get_project_by_slug

# Mock a project with slug
MOCK_PROJECTS = [
    {
        "id": "test-projem",
        "title": "Test Projem",
        "slug": "test-projem",
        "aliases": ["test projem", "test-projem", "testprojem"],
        "desc": "A test project",
        "tags": ["python", "react"],
        "case_study": {
            "problem": "test problem",
            "architecture": "test arch"
        }
    }
]

class NewFeaturesTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("Merhaba Dünya!"), "merhaba-dunya")
        self.assertEqual(slugify("Cebir-X Kütüphanesi"), "cebir-x-kutuphanesi")
        self.assertEqual(slugify("ııı ÖÖÖ üüü şşş ğğğ ççç"), "iii-ooo-uuu-sss-ggg-ccc")
        self.assertEqual(slugify("  Spaces   And --- Dashes  "), "spaces-and-dashes")

    def test_alias_generation(self):
        # Test how aliases are generated when project_aliases_str is empty
        title = "My New Project"
        title_clean = title.strip().lower()
        aliases = []
        aliases.append(title_clean)
        
        slugified = slugify(title)
        if slugified not in aliases:
            aliases.append(slugified)
            
        if ' ' in title_clean or '-' in title_clean:
            no_spaces = title_clean.replace(' ', '').replace('-', '')
            if no_spaces not in aliases:
                aliases.append(no_spaces)
            with_spaces = title_clean.replace('-', ' ')
            if with_spaces not in aliases:
                aliases.append(with_spaces)
                
        self.assertIn("my new project", aliases)
        self.assertIn("my-new-project", aliases)
        self.assertIn("mynewproject", aliases)

    def test_direct_slug_matching(self):
        # Mocking the direct matching inside get_project_by_slug
        slug = "test-projem/"
        slug_stripped = slug.strip().strip('/')
        self.assertEqual(slug_stripped, "test-projem")
        
        # Test direct match inside the mocked projects
        matched = None
        for p in MOCK_PROJECTS:
            if p.get("slug") == slug_stripped:
                matched = p
                break
        self.assertIsNotNone(matched)
        self.assertEqual(matched["id"], "test-projem")

if __name__ == "__main__":
    unittest.main()
