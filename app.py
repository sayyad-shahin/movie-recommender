"""Web app.   python app.py   then open http://127.0.0.1:5000
   python app.py --data path/to/ml-latest-small     (use MovieLens or your own movies.csv + ratings.csv)
"""
import argparse
import os

from flask import Flask, jsonify, render_template, request
from recsys import MovieRecommender, load_data, DEFAULT_DATA_DIR


def create_app(data_dir=None):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
    movies, ratings = load_data(data_dir or os.environ.get("MOVIE_DATA_DIR") or DEFAULT_DATA_DIR)
    rec = MovieRecommender(movies, ratings)

    def num(name, default, lo, hi, cast=float):
        try:
            return min(hi, max(lo, cast(request.args.get(name, default))))
        except (TypeError, ValueError):
            return default

    @app.get("/")
    def index():
        return render_template("index.html", stats=rec.stats())

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    @app.get("/api/stats")
    def stats():
        return jsonify(rec.stats())

    @app.get("/api/genres")
    def genres():
        return jsonify(rec.genres)

    @app.get("/api/movies/search")
    def search():
        return jsonify(rec.search(request.args.get("q", ""), num("limit", 8, 1, 25, int)))

    @app.get("/api/movies/<int:movie_id>/similar")
    def similar(movie_id):
        try:
            return jsonify(movie=rec.get(movie_id), results=rec.similar(
                movie_id, num("n", 10, 1, 50, int), 1 - num("audience", 0.5, 0.0, 1.0)))
        except KeyError:
            return jsonify(error="Movie not found."), 404

    @app.post("/api/recommend")
    def recommend():
        data = request.get_json(silent=True) or {}
        ratings = data.get("ratings")
        if not isinstance(ratings, dict) or not ratings or len(ratings) > 200:
            return jsonify(error="Send 'ratings' as {movie_id: rating} with 1 to 200 movies."), 400
        try:
            clean = {int(k): float(v) for k, v in ratings.items()}
            if any(not 0.5 <= v <= 5 for v in clean.values()):
                raise ValueError
            alpha = min(1.0, max(0.0, float(data.get("alpha", 0.5))))
            n = min(50, max(1, int(data.get("n", 10))))
        except (TypeError, ValueError):
            return jsonify(error="Ratings must be numbers from 1 to 5 and movie ids must be integers."), 400
        try:
            return jsonify(results=rec.recommend(clean, n, alpha))
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.get("/api/top")
    def top():
        genre = request.args.get("genre") or None
        if genre and genre not in rec.genres:
            return jsonify(error="Unknown genre."), 400
        return jsonify(rec.top_rated(genre, num("n", 10, 1, 50, int)))

    @app.get("/api/sample-user")
    def sample_user():
        return jsonify(rec.sample_user())

    return app


app = create_app()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None, help="folder with movies.csv and ratings.csv")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 5000)))
    a = ap.parse_args()
    server = create_app(a.data) if a.data else app
    print(f"Open http://127.0.0.1:{a.port} in your browser (Ctrl+C to stop)")
    server.run(host="127.0.0.1", port=a.port, debug=False)
