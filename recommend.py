"""Command-line recommender.
   python recommend.py --similar "Inception"
   python recommend.py --user 12
   python recommend.py --top --genre Comedy
   python recommend.py --rate "Inception=5" "Titanic=2" "The Matrix=5"
"""
import argparse, sys
from recsys import MovieRecommender, load_data, DEFAULT_DATA_DIR


def show(items, title):
    print(f"\n{title}\n" + "-" * len(title))
    for k, r in enumerate(items, 1):
        year = f" ({r['year']})" if r["year"] else ""
        print(f"{k:2d}. {r['title']}{year}  [{', '.join(r['genres'])}]")
        if r["reason"]:
            print(f"      {r['reason']}")


def find(rec, name):
    hits = rec.search(name, 1)
    if not hits:
        sys.exit(f"No movie found for '{name}'.")
    return hits[0]


ap = argparse.ArgumentParser()
g = ap.add_mutually_exclusive_group(required=True)
g.add_argument("--similar", metavar="TITLE", help="movies similar to this one")
g.add_argument("--user", type=int, help="recommend for a viewer id from the dataset")
g.add_argument("--top", action="store_true", help="top rated movies")
g.add_argument("--rate", nargs="+", metavar="TITLE=RATING", help='your own ratings, e.g. "Inception=5" "Titanic=2"')
ap.add_argument("--genre", help="genre filter for --top")
ap.add_argument("-n", type=int, default=10, help="how many results")
ap.add_argument("--alpha", type=float, default=0.5, help="0 = viewers' ratings only, 1 = content only")
ap.add_argument("--data", default=DEFAULT_DATA_DIR)
a = ap.parse_args()

rec = MovieRecommender(*load_data(a.data))
if a.similar:
    m = find(rec, a.similar)
    show(rec.similar(m["id"], a.n, a.alpha), f"Because you like {m['title']}")
elif a.user is not None:
    try:
        show(rec.recommend_for_user(a.user, a.n, a.alpha), f"Recommendations for viewer {a.user}")
    except KeyError as e:
        sys.exit(str(e))
elif a.top:
    show(rec.top_rated(a.genre, a.n), "Top rated" + (f" {a.genre}" if a.genre else ""))
else:
    ratings = {}
    for item in a.rate:
        name, _, val = item.rpartition("=")
        if not name:
            sys.exit(f"Use TITLE=RATING, for example \"Inception=5\" (got '{item}').")
        ratings[find(rec, name)["id"]] = float(val)
    show(rec.recommend(ratings, a.n, a.alpha), "Recommended for you")
