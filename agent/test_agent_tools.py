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

    def test_buscar_restaurantes_sp(self):
        results = buscar_restaurantes(bairro="Pinheiros")
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIn("url", r)
            self.assertIn("slug", r)
            self.assertEqual(r["neighborhood"], "Pinheiros")

    def test_obter_detalhes_restaurante_sp(self):
        details = obter_detalhes_restaurante("Antonietta Cucina")
        self.assertNotIn("erro", details)
        self.assertIn("url", details)
        self.assertIn("slug", details)
        self.assertEqual(details["slug"], "antonietta-cucina")
        self.assertEqual(details["url"], "/restaurantes/sao-paulo/antonietta-cucina")

    def test_buscar_restaurantes_sem_coords_com_cidade_sp(self):
        results = buscar_restaurantes(cidade="sp", cozinha="Italiana")
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIsNone(r["distance_km"])
            self.assertEqual(r["cuisine"], "Italiana")

    def test_buscar_restaurantes_sem_coords_com_cidade_bh(self):
        results = buscar_restaurantes(cidade="belo-horizonte", bairro="Savassi")
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIsNone(r["distance_km"])
            self.assertEqual(r["neighborhood"], "Savassi")

    def test_buscar_restaurantes_ordenacao_rating_sem_gps(self):
        results = buscar_restaurantes(cidade="sao-paulo")
        self.assertGreater(len(results), 1)
        ratings = [r["rating"] for r in results if r["rating"] is not None]
        # Verifica se as notas estão ordenadas de forma decrescente
        self.assertEqual(ratings, sorted(ratings, reverse=True))

if __name__ == "__main__":
    unittest.main()

