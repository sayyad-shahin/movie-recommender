import csv, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from recsys import MovieRecommender, load_data
import evaluate

MOVIES, RATINGS = load_data()
REC = MovieRecommender(MOVIES, RATINGS)
ID = {m.title: m.id for m in MOVIES}


class TestData(unittest.TestCase):
    def test_sample_data_loads(self):
        self.assertGreaterEqual(len(MOVIES), 100)
        self.assertGreater(len(RATINGS), 5000)
        self.assertTrue(all(0.5 <= r <= 5 for _, _, r in RATINGS))

    def test_movielens_format(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "movies.csv"), "w", newline="") as f:
                w = csv.writer(f); w.writerow(["movieId", "title", "genres"])
                w.writerow([1, "Toy Story (1995)", "Adventure|Animation|Children"])
                w.writerow([2, "Heat (1995)", "Action|Crime|Thriller"])
                w.writerow([3, "Unknown Film", "(no genres listed)"])
            with open(os.path.join(d, "ratings.csv"), "w", newline="") as f:
                w = csv.writer(f); w.writerow(["userId", "movieId", "rating", "timestamp"])
                w.writerows([[1, 1, 4.5, 0], [1, 2, 2.0, 0], [2, 1, 5.0, 0], [2, 99, 3.0, 0]])
            movies, ratings = load_data(d)
            self.assertEqual(movies[0].title, "Toy Story"); self.assertEqual(movies[0].year, 1995)
            self.assertEqual(movies[2].genres, []); self.assertEqual(len(ratings), 3)  # unknown movie 99 skipped
            rec = MovieRecommender(movies, ratings)
            self.assertEqual(len(rec.similar(1, 2)), 2)


class TestEngine(unittest.TestCase):
    def test_similar_finds_sequel(self):
        top = [r["title"] for r in REC.similar(ID["The Lord of the Rings: The Fellowship of the Ring"], 3)]
        self.assertIn("The Lord of the Rings: The Two Towers", top)

    def test_similar_excludes_itself_and_respects_n(self):
        res = REC.similar(ID["Toy Story"], 7)
        self.assertEqual(len(res), 7); self.assertNotIn("Toy Story", [r["title"] for r in res])

    def test_alpha_extremes_work(self):
        for a in (0.0, 1.0):
            self.assertEqual(len(REC.similar(ID["Heat"], 5, alpha=a)), 5)

    def test_recommend_matches_taste_and_skips_rated(self):
        mine = {ID["Inception"]: 5, ID["The Matrix"]: 5, ID["Blade Runner"]: 5, ID["Titanic"]: 1}
        res = REC.recommend(mine, 10)
        ids = {r["id"] for r in res}
        self.assertFalse(ids & set(mine))
        scifi = sum("Sci-Fi" in r["genres"] for r in res)
        self.assertGreaterEqual(scifi, 6)

    def test_animation_fan_gets_animation(self):
        res = REC.recommend({ID["Toy Story"]: 5, ID["Finding Nemo"]: 5, ID["Up"]: 5}, 8)
        self.assertGreaterEqual(sum("Animation" in r["genres"] for r in res), 5)

    def test_only_dislikes_falls_back_to_popular(self):
        self.assertEqual(len(REC.recommend({ID["Titanic"]: 1}, 5)), 5)

    def test_empty_ratings_rejected(self):
        with self.assertRaises(ValueError):
            REC.recommend({}, 5)

    def test_top_rated_genre_filter(self):
        res = REC.top_rated("Horror", 5)
        self.assertTrue(res and all("Horror" in r["genres"] for r in res))

    def test_search_exact_and_fuzzy(self):
        self.assertEqual(REC.search("godfather")[0]["title"], "The Godfather")
        self.assertEqual(REC.search("godfater")[0]["title"], "The Godfather")
        self.assertEqual(REC.search("   "), [])

    def test_recommend_for_user(self):
        uid = next(iter(REC.user_history))
        self.assertEqual(len(REC.recommend_for_user(uid, 5)), 5)

    def test_works_without_ratings(self):
        rec = MovieRecommender(MOVIES, [])
        self.assertEqual(len(rec.similar(ID["Heat"], 3)), 3)
        self.assertEqual(len(rec.recommend({ID["Heat"]: 5}, 3)), 3)


class TestEvaluation(unittest.TestCase):
    def test_personalised_beats_popularity(self):
        res = evaluate.run()
        self.assertGreater(res["Hybrid (50/50)"]["hit"], res["Popularity only"]["hit"])


class TestWebApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import create_app
        cls.c = create_app().test_client()

    def test_pages_and_basic_endpoints(self):
        self.assertEqual(self.c.get("/").status_code, 200)
        self.assertEqual(self.c.get("/api/health").get_json()["status"], "ok")
        self.assertIn("Comedy", self.c.get("/api/genres").get_json())
        self.assertGreater(self.c.get("/api/stats").get_json()["movies"], 100)

    def test_search_and_similar(self):
        hit = self.c.get("/api/movies/search?q=inception").get_json()[0]
        d = self.c.get(f"/api/movies/{hit['id']}/similar?n=5&audience=0.3").get_json()
        self.assertEqual(len(d["results"]), 5)
        self.assertEqual(self.c.get("/api/movies/999999/similar").status_code, 404)

    def test_recommend_endpoint(self):
        r = self.c.post("/api/recommend", json={"ratings": {str(ID["Inception"]): 5}, "n": 4})
        self.assertEqual(r.status_code, 200); self.assertEqual(len(r.get_json()["results"]), 4)
        for bad in ({}, {"ratings": {}}, {"ratings": {"1": 9}}, {"ratings": {"abc": 3}}, {"ratings": [1, 2]}):
            self.assertEqual(self.c.post("/api/recommend", json=bad).status_code, 400, bad)

    def test_top_and_sample(self):
        self.assertEqual(len(self.c.get("/api/top?genre=Comedy&n=3").get_json()), 3)
        self.assertEqual(self.c.get("/api/top?genre=Nope").status_code, 400)
        self.assertTrue(self.c.get("/api/sample-user").get_json()["ratings"])


if __name__ == "__main__":
    unittest.main()
