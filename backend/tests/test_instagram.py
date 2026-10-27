import unittest
from app.instagram import normalize_instagram_url


class InstagramUrlTests(unittest.TestCase):
    def test_post(self):
        self.assertEqual(normalize_instagram_url("https://instagram.com/p/ABCdef12/?igsh=abc"),
                         ("https://www.instagram.com/p/ABCdef12/", "ABCdef12", "post"))

    def test_reel(self):
        self.assertEqual(normalize_instagram_url("https://www.instagram.com/reel/ABCdef12/")[2], "reel")

    def test_trailing_query_stripped(self):
        url, _, _ = normalize_instagram_url("https://m.instagram.com/p/ABCdef12/?utm_source=test")
        self.assertEqual(url, "https://www.instagram.com/p/ABCdef12/")

    def test_host_substitution_rejected(self):
        for url in ["https://instagram.com.evil.test/p/ABCdef12/",
                    "https://evil.test/p/ABCdef12/", "http://instagram.com/p/ABCdef12/",
                    "https://www.instagram.com/@username/",
                    "https://www.instagram.com/p/ABCdef12/extra",
                    "https://www.instagram.com/p/../"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                normalize_instagram_url(url)


if __name__ == "__main__":
    unittest.main()
