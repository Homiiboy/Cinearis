"""Fast-running tests of candidate parsing, without API keys or image uploads."""
import unittest
from app.analysis import Candidate, combine_candidates, ocr_candidates, parse_vision_response


class AnalysisTests(unittest.TestCase):
    def test_ocr_candidates_are_low_confidence(self):
        result = ocr_candidates("ONE PIECE\nNaruto\nONE PIECE\n")
        self.assertEqual(len(result), 2)
        self.assertTrue(all(c.confidence < 0.7 for c in result))
        self.assertTrue(all(c.kind == "unknown" for c in result))

    def test_duplicates_prefer_vision(self):
        ocr = Candidate(title="One Piece", source="ocr", kind="unknown", confidence=0.35)
        vision = Candidate(title="one piece", source="vision", kind="anime", confidence=0.95)
        results = combine_candidates([ocr, vision])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["kind"], "anime")

    def test_invalid_candidates_ignored(self):
        data = {"titles": [
            {"title": "Naruto", "kind": "anime", "confidence": 0.93},
            {"title": "", "kind": "movie", "confidence": 1},
            {"title": "Invalid", "kind": "bad-kind", "confidence": 0.8},
        ]}
        result = parse_vision_response(data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Naruto")

    def test_empty_response(self):
        self.assertEqual(parse_vision_response(None), [])


if __name__ == "__main__":
    unittest.main()
