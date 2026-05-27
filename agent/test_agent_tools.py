import unittest
from agent.tools import buscar_restaurantes, obter_detalhes_restaurante

class TestAgentTools(unittest.TestCase):
    def test_buscar_restaurantes_includes_slug_and_url(self):
        results = buscar_restaurantes(cozinha="Italiana")
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIn("url", r)
            self.assertIn("slug", r)
            self.assertTrue(r["url"].startswith("/restaurantes/"))
            self.assertFalse(r["slug"].endswith("/"))
            self.assertNotIn("/", r["slug"])

    def test_obter_detalhes_restaurante_includes_slug_and_url(self):
        details = obter_detalhes_restaurante("477 Pizzeria")
        self.assertNotIn("erro", details)
        self.assertIn("url", details)
        self.assertIn("slug", details)
        self.assertEqual(details["slug"], "477-pizzeria")
        self.assertEqual(details["url"], "/restaurantes/belo-horizonte/477-pizzeria")

if __name__ == "__main__":
    unittest.main()
