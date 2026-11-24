"""The recommendation engine (NumPy / SciPy / scikit-learn).

Two ways of finding movies you may like:
  * CONTENT-BASED: movies with similar genres, director, title words and story keywords (TF-IDF + cosine similarity).
  * COLLABORATIVE (item-based): movies that the same viewers tended to rate above their own average (adjusted cosine).
The HYBRID mixes both: score = alpha * content + (1 - alpha) * collaborative (+ a small popularity prior).
"""
import csv
import difflib
import os
import random
import re
from dataclasses import dataclass, field

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATA_DIR = os.path.join(ROOT, "data")
YEAR_RE = re.compile(r"\s*\((\d{4})\)\s*$")


@dataclass
class Movie:
    id: int
    title: str
    year: object = None
    genres: list = field(default_factory=list)
    director: str = ""
    overview: str = ""


def load_data(data_dir=DEFAULT_DATA_DIR):
    """Read movies.csv and ratings.csv. Works with this project's files and with MovieLens (ml-latest-small).

    movies.csv : movieId,title,genres[,director,overview]   (genres separated by |, year in the title like "Heat (1995)")
    ratings.csv: userId,movieId,rating[,timestamp]
    """
    movies, ids = [], set()
    with open(os.path.join(data_dir, "movies.csv"), newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            raw = row["title"].strip()
            m = YEAR_RE.search(raw)
            genres = [g.strip() for g in row["genres"].split("|") if g.strip() and g.strip() != "(no genres listed)"]
            movies.append(Movie(int(row["movieId"]), YEAR_RE.sub("", raw), int(m.group(1)) if m else None, genres,
                                (row.get("director") or "").strip(), (row.get("overview") or "").strip()))
            ids.add(int(row["movieId"]))
    ratings = []
    rpath = os.path.join(data_dir, "ratings.csv")
    if os.path.exists(rpath):
        with open(rpath, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                mid = int(row["movieId"])
                if mid in ids:
                    ratings.append((int(row["userId"]), mid, float(row["rating"])))
    return movies, ratings


def _tok(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _norm(x):
    """Scale scores so the best one is 1.0 (negative values become 0)."""
    x = np.clip(x, 0, None)
    top = x.max() if len(x) else 0
    return x / top if top > 0 else x


class MovieRecommender:
    def __init__(self, movies, ratings, shrink=5.0, min_votes=10):
        if not movies:
            raise ValueError("No movies to recommend from.")
        self.movies = list(movies)
        self.n = len(self.movies)
        self.idx = {m.id: i for i, m in enumerate(self.movies)}
        self.shrink = shrink
        self.genres = sorted({g for m in self.movies for g in m.genres})
        self._cf_cache, self._content_cache = {}, {}
        self._build_content()
        self._build_collaborative(ratings)
        self._build_popularity(min_votes)

    # ------------------------------------------------------------------ building
    def _build_content(self):
        docs = []
        for m in self.movies:
            genre_part = " ".join(f"g_{_tok(g)}" for g in m.genres)
            director = f"d_{_tok(m.director)} " * 2 if m.director else ""
            docs.append(f"{m.overview} {m.title} {director}{(genre_part + ' ') * 3}")
        self.tfidf = TfidfVectorizer(stop_words="english", sublinear_tf=True).fit_transform(docs).tocsr()

    def _build_collaborative(self, ratings):
        users, rows, cols, vals = {}, [], [], []
        self.user_history = {}
        for u, mid, r in ratings:
            j = self.idx.get(mid)
            if j is None:
                continue
            rows.append(users.setdefault(u, len(users)))
            cols.append(j)
            vals.append(float(r))
            self.user_history.setdefault(u, {})[mid] = float(r)
        self.n_users, self.n_ratings = len(users), len(vals)
        self.item_u = None
        self.votes = np.zeros(self.n)
        self.avg_rating = np.zeros(self.n)
        if not vals:
            return
        shape = (self.n_users, self.n)
        R = sparse.csr_matrix((vals, (rows, cols)), shape=shape)
        B = sparse.csr_matrix((np.ones(len(vals)), (rows, cols)), shape=shape)
        counts = np.asarray(B.sum(axis=1)).ravel()
        means = np.asarray(R.sum(axis=1)).ravel() / np.maximum(counts, 1)
        coo = R.tocoo()
        centered = sparse.csr_matrix((coo.data - means[coo.row], (coo.row, coo.col)), shape=shape)
        self.item_u = centered.T.tocsr()            # items x users, ratings minus each user's own average
        self.item_b = B.T.tocsr()                   # items x users, 1 where rated
        self.item_norm = np.sqrt(np.asarray(self.item_u.multiply(self.item_u).sum(axis=1)).ravel())
        self.votes = np.asarray(B.sum(axis=0)).ravel()
        self.avg_rating = np.asarray(R.sum(axis=0)).ravel() / np.maximum(self.votes, 1)

    def _build_popularity(self, min_votes):
        """IMDb-style weighted rating: items with few votes are pulled toward the global average."""
        total = self.votes.sum()
        global_mean = (self.avg_rating * self.votes).sum() / total if total else 0.0
        v = self.votes
        self.pop = (v / (v + min_votes)) * self.avg_rating + (min_votes / (v + min_votes)) * global_mean
        span = self.pop.max() - self.pop.min()
        self.pop01 = (self.pop - self.pop.min()) / span if span > 0 else np.zeros(self.n)

    # ------------------------------------------------------------------ similarity rows
    def content_row(self, i):
        if i not in self._content_cache:
            if len(self._content_cache) > 400:
                self._content_cache.clear()
            row = (self.tfidf @ self.tfidf[i].T).toarray().ravel()
            row[i] = 0.0
            self._content_cache[i] = row
        return self._content_cache[i]

    def cf_row(self, i):
        """How similar movie i is to every movie, judged by viewers' ratings (0 if there is no rating data)."""
        if self.item_u is None:
            return np.zeros(self.n)
        if i not in self._cf_cache:
            if len(self._cf_cache) > 400:
                self._cf_cache.clear()
            dots = (self.item_u[i] @ self.item_u.T).toarray().ravel()
            common = (self.item_b[i] @ self.item_b.T).toarray().ravel()
            denom = self.item_norm[i] * self.item_norm
            sim = np.divide(dots, denom, out=np.zeros(self.n), where=denom > 0)
            sim *= common / (common + self.shrink)   # distrust similarities based on few shared viewers
            sim[i] = 0.0
            self._cf_cache[i] = sim
        return self._cf_cache[i]

    # ------------------------------------------------------------------ helpers
    def _movie_dict(self, j, score=None, reason=""):
        m = self.movies[j]
        return {"id": m.id, "title": m.title, "year": m.year, "genres": m.genres, "director": m.director,
                "overview": m.overview, "avg_rating": round(float(self.avg_rating[j]), 2) if self.votes[j] else None,
                "votes": int(self.votes[j]), "score": None if score is None else round(float(score), 3), "reason": reason}

    @staticmethod
    def _top(scores, n, exclude=()):
        s = np.array(scores, dtype=float)
        for e in exclude:
            s[e] = -np.inf
        order = np.argsort(-s, kind="stable")[:n]
        return [int(j) for j in order if np.isfinite(s[j])]

    def get(self, movie_id):
        if movie_id not in self.idx:
            raise KeyError(f"Unknown movie id {movie_id}")
        return self._movie_dict(self.idx[movie_id])

    # ------------------------------------------------------------------ public API
    def similar(self, movie_id, n=10, alpha=0.5):
        """Movies similar to one movie. alpha = weight of content (1.0 = content only, 0.0 = viewers' ratings only)."""
        if movie_id not in self.idx:
            raise KeyError(f"Unknown movie id {movie_id}")
        i = self.idx[movie_id]
        cf = self.cf_row(i)
        score = alpha * _norm(self.content_row(i)) + (1 - alpha) * _norm(cf)
        out = []
        for j in self._top(score, n, exclude=[i]):
            a, b = self.movies[i], self.movies[j]
            parts = []
            shared = [g for g in b.genres if g in a.genres]
            if shared:
                parts.append("Shared genres: " + ", ".join(shared))
            if a.director and a.director == b.director:
                parts.append(f"Same director ({a.director})")
            if cf[j] > 0.15:
                parts.append("Viewers who liked one often liked the other")
            out.append(self._movie_dict(j, score[j], "; ".join(parts) or "Similar story and themes"))
        return out

    def recommend(self, ratings, n=10, alpha=0.5, pop_weight=0.1):
        """Personalised picks from {movie_id: rating 1-5}. Ratings above 3 attract, below 3 repel."""
        rated = {self.idx[int(m)]: float(r) for m, r in ratings.items() if int(m) in self.idx}
        if not rated:
            raise ValueError("Rate at least one movie first.")
        w = {i: r - 3.0 for i, r in rated.items()}
        if not any(v > 0 for v in w.values()):
            return self.recommend_popular(ratings, n)
        weights = np.zeros(self.n)
        for i, v in w.items():
            weights[i] = v
        profile = sparse.csr_matrix(weights) @ self.tfidf                    # taste profile in word space
        content = (self.tfidf @ profile.T).toarray().ravel()
        cf = np.zeros(self.n)
        for i, v in w.items():
            cf += v * np.clip(self.cf_row(i), 0, None)
        score = alpha * _norm(content) + (1 - alpha) * _norm(cf) + pop_weight * self.pop01
        liked = sorted((i for i, v in w.items() if v > 0), key=lambda i: -w[i])[:15]
        out = []
        for j in self._top(score, n, exclude=rated):
            ranked = sorted(liked, key=lambda i: -(w[i] * (alpha * self.content_row(i)[j] + (1 - alpha) * max(self.cf_row(i)[j], 0))))
            because = [self.movies[i].title for i in ranked[:2]
                       if alpha * self.content_row(i)[j] + (1 - alpha) * max(self.cf_row(i)[j], 0) > 0]
            reason = "Because you liked " + " and ".join(because) if because else "Popular with viewers like you"
            out.append(self._movie_dict(j, score[j], reason))
        return out

    def recommend_popular(self, ratings=None, n=10):
        rated = {self.idx[int(m)] for m in (ratings or {}) if int(m) in self.idx}
        return [self._movie_dict(j, self.pop01[j], "Highly rated by many viewers")
                for j in self._top(self.pop, n, exclude=rated)]

    def recommend_for_user(self, user_id, n=10, alpha=0.5):
        if user_id not in self.user_history:
            raise KeyError(f"Unknown user {user_id}")
        return self.recommend(self.user_history[user_id], n, alpha)

    def top_rated(self, genre=None, n=10):
        pool = [j for j in range(self.n) if not genre or genre in self.movies[j].genres]
        order = sorted(pool, key=lambda j: -self.pop[j])[:n]
        return [self._movie_dict(j, self.pop01[j], "Top rated" + (f" in {genre}" if genre else "")) for j in order]

    def search(self, query, limit=8):
        q = query.strip().lower()
        if not q:
            return []
        titles = [m.title.lower() for m in self.movies]
        hits = [i for i, t in enumerate(titles) if t.startswith(q)]
        hits += [i for i, t in enumerate(titles) if q in t and i not in hits]
        if len(hits) < limit:
            for t in difflib.get_close_matches(q, titles, n=limit, cutoff=0.6):
                i = titles.index(t)
                if i not in hits:
                    hits.append(i)
        return [self._movie_dict(i) for i in hits[:limit]]

    def sample_user(self, seed=None, how_many=8):
        """A random viewer's favourite films, handy for trying the recommender."""
        rng = random.Random(seed)
        uid = rng.choice(sorted(self.user_history))
        favs = sorted(self.user_history[uid].items(), key=lambda kv: -kv[1])
        favs = [kv for kv in favs if kv[1] >= 4][:how_many]
        return {"user_id": uid, "ratings": [{**self.get(m), "rating": int(r)} for m, r in favs]}

    def stats(self):
        return {"movies": self.n, "users": self.n_users, "ratings": self.n_ratings, "genres": self.genres}
