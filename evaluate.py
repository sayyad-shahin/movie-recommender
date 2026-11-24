"""Measure how good the recommendations are with a hold-out test.

For every viewer we hide 20% of their ratings, recommend 10 movies using the rest, and check how many of the
hidden movies they liked (rated 4 or 5) show up in the list.
   python evaluate.py [--data data] [--k 10]
"""
import argparse
import random

import numpy as np
from recsys import MovieRecommender, load_data, DEFAULT_DATA_DIR


def split(ratings, test_frac=0.2, seed=0):
    rng = random.Random(seed)
    by_user = {}
    for u, m, r in ratings:
        by_user.setdefault(u, []).append((m, r))
    train, test = [], {}
    for u, items in by_user.items():
        rng.shuffle(items)
        cut = max(1, int(len(items) * test_frac))
        test[u] = items[:cut]
        train += [(u, m, r) for m, r in items[cut:]]
    return train, test


def run(data_dir=DEFAULT_DATA_DIR, k=10, seed=0):
    movies, ratings = load_data(data_dir)
    train, test = split(ratings, seed=seed)
    rec = MovieRecommender(movies, train)
    methods = {
        "Popularity only": lambda r: rec.recommend_popular(r, k),
        "Content-based": lambda r: rec.recommend(r, k, alpha=1.0, pop_weight=0.0),
        "Collaborative": lambda r: rec.recommend(r, k, alpha=0.0, pop_weight=0.0),
        "Hybrid (50/50)": lambda r: rec.recommend(r, k, alpha=0.5),
    }
    scores = {name: {"precision": [], "recall": [], "hit": []} for name in methods}
    for u, held in test.items():
        relevant = {m for m, r in held if r >= 4}
        history = rec.user_history.get(u, {})
        if not relevant or len(history) < 5:
            continue
        for name, fn in methods.items():
            got = {x["id"] for x in fn(history)}
            hits = len(got & relevant)
            scores[name]["precision"].append(hits / k)
            scores[name]["recall"].append(hits / len(relevant))
            scores[name]["hit"].append(1.0 if hits else 0.0)
    return {name: {m: float(np.mean(v)) for m, v in s.items()} | {"viewers": len(s["hit"])} for name, s in scores.items()}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DEFAULT_DATA_DIR)
    ap.add_argument("--k", type=int, default=10)
    a = ap.parse_args()
    res = run(a.data, a.k)
    first = next(iter(res.values()))
    print(f"Hold-out test on {first['viewers']} viewers, top {a.k} recommendations each\n")
    print(f"{'Method':<18}{'Precision@' + str(a.k):>14}{'Recall@' + str(a.k):>12}{'Hit rate':>11}")
    for name, s in res.items():
        print(f"{name:<18}{s['precision']:>14.3f}{s['recall']:>12.3f}{s['hit']:>11.3f}")
