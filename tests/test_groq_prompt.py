import unittest

from harun_site.utils.groq_client import _SYSTEM_PROMPT_TEMPLATE_TR, _SYSTEM_PROMPT_TEMPLATE_EN


class GroqPromptTests(unittest.TestCase):
    def test_registry_guardrail_exists(self):
        for template in (_SYSTEM_PROMPT_TEMPLATE_TR, _SYSTEM_PROMPT_TEMPLATE_EN):
            self.assertIn(
                "Project names and URLs are immutable registry-controlled identifiers.",
                template,
            )

    def test_token_instruction_exists(self):
        for template in (_SYSTEM_PROMPT_TEMPLATE_TR, _SYSTEM_PROMPT_TEMPLATE_EN):
            self.assertIn("[[PROJECT_REF:<project_id>]]", template)


if __name__ == "__main__":
    unittest.main()