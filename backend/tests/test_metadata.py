"""Phase 3 unit tests: deterministic metadata mapping without network access."""
import unittest
from app.metadata import anime_result, cleaned_names, normalized, relevance, tmdb_result


class MetadataTests(unittest.TestCase):
    def test_german_unicode_normalization(self):
        self.assertEqual(normalized("König der Löwen"), "konig der lowen")

    def test_exact_alias_wins(self):
        self.assertEqual(relevance("Shingeki no Kyojin", ["Attack on Titan", "Shingeki no Kyojin"]), 1.0)

    def test_english_and_original_titles(self):
        entry = anime_result({"id": 16498, "title": {"english": "Attack on Titan", "romaji": "Shingeki no Kyojin", "native": "進撃の巨人"}, "synonyms": ["AoT"], "startDate": {"year": 2013}, "coverImage": {"medium": "https://img.example/test.jpg"}})
        self.assertEqual(entry["provider_id"], "16498")
        self.assertEqual(entry["original_title"], "Shingeki no Kyojin")
        self.assertIn("AoT", entry["aliases"])
        self.assertEqual(entry["release_year"], 2013)

    def test_tmdb_movie(self):
        entry = tmdb_result({"id": 123, "title": "Der König der Löwen", "original_title": "The Lion King", "release_date": "1994-06-15", "poster_path": "/abc.jpg"}, "movie")
        self.assertEqual(entry["kind"], "movie")
        self.assertIn("The Lion King", entry["aliases"])
        self.assertEqual(entry["release_year"], 1994)

    def test_alias_deduplication(self):
        self.assertEqual(cleaned_names("Naruto", ["Naruto", "ナルト"]), ["Naruto", "ナルト"])


if __name__ == "__main__":
    unittest.main()
