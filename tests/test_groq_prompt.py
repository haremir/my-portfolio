import unittest

from harun_site.utils.groq_client import _SYSTEM_PROMPT_TEMPLATE


class GroqPromptTests(unittest.TestCase):
    def test_registry_guardrail_exists(self):
        self.assertIn(
            "Project names and URLs are immutable registry-controlled identifiers.",
            _SYSTEM_PROMPT_TEMPLATE,
        )

    def test_token_instruction_exists(self):
        self.assertIn("[[PROJECT_REF:<project_id>]]", _SYSTEM_PROMPT_TEMPLATE)


if __name__ == "__main__":
    unittest.main()