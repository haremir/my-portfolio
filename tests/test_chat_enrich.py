import unittest

from harun_site.utils.chat_enrich import (
    finalize_project_references,
    finalize_streamed_project_references,
)


class ChatEnrichTests(unittest.TestCase):
    def test_token_renders_canonical_link(self):
        text = "Projeye bak: [[PROJECT_REF:cebirx]]"
        rendered = finalize_project_references(text, "cebirx")
        self.assertIn("[CebirX](/portfolio/cebirx)", rendered)
        self.assertNotIn("PROJECT_REF", rendered)
        self.assertNotIn("/portfolio/cebrix", rendered)

    def test_bad_slug_is_canonicalized(self):
        text = "Detay: [Cebrix](/portfolio/cebrix)"
        rendered = finalize_project_references(text, "cebirx")
        self.assertIn("[CebirX](/portfolio/cebirx)", rendered)
        self.assertNotIn("/portfolio/cebrix", rendered)

    def test_raw_bad_url_is_canonicalized(self):
        text = "Detay: /portfolio/cebix"
        rendered = finalize_project_references(text, "cebirx")
        self.assertIn("/portfolio/cebirx", rendered)
        self.assertNotIn("/portfolio/cebix", rendered)

    def test_plain_text_project_name_is_canonicalized(self):
        text = "Best project is Cebrix"
        rendered = finalize_project_references(text, "cebirx")
        self.assertIn("CebirX", rendered)
        self.assertNotIn("Cebrix", rendered)

    def test_chunked_stream_finalizes_only_after_join(self):
        chunks = ["[Case Study](/portfolio/ceb", "rix)"]
        rendered = finalize_streamed_project_references(chunks, "cebirx")
        self.assertIn("/portfolio/cebirx", rendered)
        self.assertNotIn("/portfolio/cebrix", rendered)
        self.assertNotIn("cebrix", rendered.lower())


if __name__ == "__main__":
    unittest.main()