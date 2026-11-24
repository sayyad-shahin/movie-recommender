"""Create the SAMPLE dataset: data/movies.csv (108 real films) and data/ratings.csv (synthetic viewers).

The film list (titles, years, genres, directors) is real. The one-line descriptions are written for this project.
The RATINGS ARE SYNTHETIC: 400 made-up viewers with different tastes, so collaborative filtering has something to learn.
Use real data (e.g. MovieLens) for a real system. See README.
"""
import argparse, csv, os, random

# (title, year, genres, director, overview, acclaim 1-10 used only to shape the synthetic ratings)
MOVIES = [
("Toy Story",1995,"Adventure|Animation|Children|Comedy","John Lasseter","A cowboy doll feels threatened when a new space ranger toy joins the kid's collection.",8.3),
("The Shawshank Redemption",1994,"Crime|Drama","Frank Darabont","A banker wrongly jailed for murder finds hope and friendship inside prison walls.",9.3),
("The Godfather",1972,"Crime|Drama","Francis Ford Coppola","An aging mafia patriarch passes control of his crime family to his reluctant son.",9.2),
("The Dark Knight",2008,"Action|Crime|Drama","Christopher Nolan","Batman faces a chaotic criminal mastermind who pushes Gotham to its breaking point.",9.0),
("Pulp Fiction",1994,"Comedy|Crime|Thriller","Quentin Tarantino","Interlocking stories of hitmen, a boxer and gangsters in Los Angeles.",8.9),
("Forrest Gump",1994,"Comedy|Drama|Romance","Robert Zemeckis","A kind-hearted man unwittingly takes part in decades of American history.",8.8),
("Inception",2010,"Action|Sci-Fi|Thriller","Christopher Nolan","A thief who steals secrets through dreams is hired to plant an idea instead.",8.8),
("The Matrix",1999,"Action|Sci-Fi","The Wachowskis","A hacker discovers reality is a simulation and joins a rebellion against machines.",8.7),
("Fight Club",1999,"Drama|Thriller","David Fincher","A bored office worker and a charismatic stranger start an underground fight club.",8.8),
("Goodfellas",1990,"Crime|Drama","Martin Scorsese","A young man rises through the ranks of the mob and watches it unravel.",8.7),
("Star Wars: Episode IV - A New Hope",1977,"Action|Adventure|Sci-Fi","George Lucas","A farm boy joins rebels to fight an evil empire and rescue a princess.",8.6),
("The Empire Strikes Back",1980,"Action|Adventure|Sci-Fi","Irvin Kershner","Rebels are hunted across the galaxy while a young Jedi trains and faces his destiny.",8.7),
("Raiders of the Lost Ark",1981,"Action|Adventure","Steven Spielberg","An archaeologist races Nazis to find a legendary ark with supernatural power.",8.4),
("Jurassic Park",1993,"Adventure|Sci-Fi|Thriller","Steven Spielberg","Cloned dinosaurs escape on a theme park island and hunt the visitors.",8.2),
("Schindler's List",1993,"Drama|War","Steven Spielberg","A businessman saves over a thousand Jewish workers during the Holocaust.",9.0),
("Saving Private Ryan",1998,"Action|Drama|War","Steven Spielberg","A squad of soldiers is sent behind enemy lines to bring one man home.",8.6),
("Titanic",1997,"Drama|Romance","James Cameron","A young couple from different classes fall in love aboard a doomed ocean liner.",7.9),
("Terminator 2: Judgment Day",1991,"Action|Sci-Fi","James Cameron","A reprogrammed cyborg protects a boy from a more advanced killing machine.",8.6),
("Aliens",1986,"Action|Horror|Sci-Fi","James Cameron","Survivor Ripley returns with marines to a planet overrun by deadly creatures.",8.4),
("Alien",1979,"Horror|Sci-Fi","Ridley Scott","A space crew is stalked by a deadly creature aboard their ship.",8.5),
("Blade Runner",1982,"Sci-Fi|Thriller","Ridley Scott","A detective hunts rogue androids in a rain soaked futuristic city.",8.1),
("Gladiator",2000,"Action|Adventure|Drama","Ridley Scott","A betrayed Roman general becomes a gladiator and seeks revenge on the emperor.",8.5),
("The Lord of the Rings: The Fellowship of the Ring",2001,"Adventure|Fantasy","Peter Jackson","A hobbit and his allies set out to destroy a powerful ring.",8.8),
("The Lord of the Rings: The Two Towers",2002,"Adventure|Fantasy","Peter Jackson","The fellowship is split as war comes to the kingdoms of Middle-earth.",8.8),
("The Lord of the Rings: The Return of the King",2003,"Action|Adventure|Fantasy","Peter Jackson","The final battle for Middle-earth begins as the ring nears the fires of Mount Doom.",9.0),
("Back to the Future",1985,"Adventure|Comedy|Sci-Fi","Robert Zemeckis","A teenager travels to the past in a time machine and risks erasing his own existence.",8.5),
("The Silence of the Lambs",1991,"Crime|Horror|Thriller","Jonathan Demme","A young FBI trainee seeks help from an imprisoned cannibal to catch a killer.",8.6),
("Se7en",1995,"Crime|Mystery|Thriller","David Fincher","Two detectives track a serial killer whose murders follow the seven deadly sins.",8.6),
("The Usual Suspects",1995,"Crime|Mystery|Thriller","Bryan Singer","Survivors of a heist gone wrong tell a tale of a mythical crime lord.",8.5),
("Casablanca",1942,"Drama|Romance|War","Michael Curtiz","A cynical club owner in wartime Morocco must choose between love and virtue.",8.5),
("Psycho",1960,"Horror|Mystery|Thriller","Alfred Hitchcock","A thief on the run checks into an isolated motel run by a strange young man.",8.5),
("Vertigo",1958,"Mystery|Romance|Thriller","Alfred Hitchcock","A retired detective with a fear of heights becomes obsessed with a mysterious woman.",8.3),
("Rear Window",1954,"Mystery|Thriller","Alfred Hitchcock","A photographer stuck in his apartment suspects a neighbor of murder.",8.5),
("Citizen Kane",1941,"Drama|Mystery","Orson Welles","Reporters investigate the meaning of a dying tycoon's last word.",8.3),
("12 Angry Men",1957,"Crime|Drama","Sidney Lumet","A lone juror argues against a hasty guilty verdict in a murder trial.",9.0),
("Spirited Away",2001,"Adventure|Animation|Fantasy","Hayao Miyazaki","A girl must work in a bathhouse for spirits to free her parents.",8.6),
("My Neighbor Totoro",1988,"Animation|Children|Fantasy","Hayao Miyazaki","Two sisters move to the countryside and meet gentle forest spirits.",8.1),
("Princess Mononoke",1997,"Action|Adventure|Animation|Fantasy","Hayao Miyazaki","A young warrior is caught in a struggle between forest gods and an iron town.",8.3),
("The Lion King",1994,"Animation|Children|Drama","Roger Allers","A young lion prince flees his kingdom after his father's death and must return.",8.5),
("Finding Nemo",2003,"Adventure|Animation|Children|Comedy","Andrew Stanton","A timid clownfish crosses the ocean to find his lost son.",8.2),
("Up",2009,"Adventure|Animation|Children|Drama","Pete Docter","An elderly widower ties balloons to his house and flies to South America.",8.3),
("WALL-E",2008,"Adventure|Animation|Children|Sci-Fi","Andrew Stanton","A lonely trash compacting robot follows a probe into space and saves humanity.",8.4),
("Shrek",2001,"Adventure|Animation|Children|Comedy|Fantasy","Andrew Adamson","A grumpy ogre rescues a princess to get his swamp back.",7.9),
("The Incredibles",2004,"Action|Adventure|Animation|Children","Brad Bird","A family of retired superheroes is pulled back into action to stop a villain.",8.0),
("Monsters, Inc.",2001,"Adventure|Animation|Children|Comedy","Pete Docter","Monsters who power their city with children's screams befriend a little girl.",8.1),
("Coco",2017,"Adventure|Animation|Children|Fantasy","Lee Unkrich","A boy who dreams of music travels to the land of the dead.",8.4),
("Spider-Man: Into the Spider-Verse",2018,"Action|Adventure|Animation|Sci-Fi","Bob Persichetti","A teenager meets Spider-People from other dimensions and learns to be a hero.",8.4),
("The Avengers",2012,"Action|Adventure|Sci-Fi","Joss Whedon","Earth's mightiest heroes team up to stop an alien invasion led by Loki.",8.0),
("Iron Man",2008,"Action|Adventure|Sci-Fi","Jon Favreau","A billionaire inventor builds a powered suit to escape captivity and fight evil.",7.9),
("Guardians of the Galaxy",2014,"Action|Adventure|Comedy|Sci-Fi","James Gunn","A band of misfit outlaws joins forces to protect a powerful orb.",8.0),
("Black Panther",2018,"Action|Adventure|Sci-Fi","Ryan Coogler","A new king of a hidden African nation faces a challenge to his throne.",7.3),
("Mad Max: Fury Road",2015,"Action|Adventure|Sci-Fi","George Miller","A drifter and a rebel soldier flee a tyrant across a desert in armored vehicles.",8.1),
("Die Hard",1988,"Action|Thriller","John McTiernan","An off duty cop fights terrorists who take over a Los Angeles skyscraper.",8.2),
("The Terminator",1984,"Action|Sci-Fi|Thriller","James Cameron","A cyborg assassin is sent back in time to kill the mother of a future leader.",8.1),
("Leon: The Professional",1994,"Action|Crime|Drama","Luc Besson","A hitman reluctantly protects a young girl whose family was murdered.",8.5),
("Heat",1995,"Action|Crime|Thriller","Michael Mann","A veteran detective and a master thief wage a cat and mouse game.",8.3),
("The Departed",2006,"Crime|Drama|Thriller","Martin Scorsese","An undercover cop and a mole in the police race to expose each other.",8.5),
("No Country for Old Men",2007,"Crime|Drama|Thriller","Joel and Ethan Coen","A hunter finds drug money and is chased by a relentless killer.",8.2),
("Fargo",1996,"Comedy|Crime|Thriller","Joel and Ethan Coen","A car salesman's botched kidnapping plot draws a pregnant police chief into the case.",8.1),
("The Big Lebowski",1998,"Comedy|Crime","Joel and Ethan Coen","A laid back bowler is dragged into a kidnapping scheme by mistaken identity.",8.1),
("Groundhog Day",1993,"Comedy|Fantasy|Romance","Harold Ramis","A cynical weatherman is trapped reliving the same day over and over.",8.0),
("Ferris Bueller's Day Off",1986,"Comedy","John Hughes","A clever teenager skips school for a day of adventures in Chicago.",7.8),
("The Breakfast Club",1985,"Comedy|Drama","John Hughes","Five very different students spend a Saturday detention and discover what they share.",7.8),
("Superbad",2007,"Comedy","Greg Mottola","Two awkward teenagers try to get alcohol for a party before graduation.",7.6),
("Bridesmaids",2011,"Comedy|Romance","Paul Feig","A maid of honor's life unravels as she competes with the bride's new friend.",6.8),
("The Hangover",2009,"Comedy","Todd Phillips","Three friends wake up from a wild bachelor party and cannot find the groom.",7.7),
("Monty Python and the Holy Grail",1975,"Adventure|Comedy|Fantasy","Terry Gilliam and Terry Jones","King Arthur and his knights bumble through a silly quest for the grail.",8.2),
("Airplane!",1980,"Comedy","Jim Abrahams","A former pilot must land a passenger plane after the crew falls ill.",7.7),
("When Harry Met Sally...",1989,"Comedy|Romance","Rob Reiner","Two friends debate whether men and women can be friends without romance.",7.7),
("Pride & Prejudice",2005,"Drama|Romance","Joe Wright","A spirited young woman and a proud gentleman misjudge each other in Regency England.",7.8),
("The Notebook",2004,"Drama|Romance","Nick Cassavetes","A poor young man and a wealthy girl fall in love across the years.",7.8),
("La La Land",2016,"Comedy|Drama|Musical|Romance","Damien Chazelle","A jazz pianist and an aspiring actress chase dreams and love in Los Angeles.",8.0),
("Whiplash",2014,"Drama","Damien Chazelle","A young drummer is pushed to extremes by a ruthless music teacher.",8.5),
("The Sound of Music",1965,"Drama|Musical|Romance","Robert Wise","A governess brings song to a strict captain's children as war approaches.",8.1),
("Singin' in the Rain",1952,"Comedy|Musical|Romance","Gene Kelly and Stanley Donen","A silent film star and his partner struggle to adapt when movies learn to talk.",8.3),
("Amelie",2001,"Comedy|Romance","Jean-Pierre Jeunet","A shy Parisian waitress secretly improves the lives of people around her.",8.3),
("Parasite",2019,"Comedy|Drama|Thriller","Bong Joon-ho","A poor family schemes its way into the lives of a wealthy household.",8.5),
("Oldboy",2003,"Action|Mystery|Thriller","Park Chan-wook","A man imprisoned for fifteen years without explanation sets out for revenge.",8.4),
("Pan's Labyrinth",2006,"Drama|Fantasy|War","Guillermo del Toro","A girl escapes the cruelty of postwar Spain into a dark fantasy world.",8.2),
("City of God",2002,"Crime|Drama","Fernando Meirelles","Two boys take different paths amid gang violence in a Rio de Janeiro slum.",8.6),
("Seven Samurai",1954,"Action|Adventure|Drama","Akira Kurosawa","A poor village hires wandering warriors to defend it from bandits.",8.6),
("Interstellar",2014,"Adventure|Drama|Sci-Fi","Christopher Nolan","Astronauts travel through a wormhole to find a new home for humanity.",8.7),
("The Prestige",2006,"Drama|Mystery|Sci-Fi|Thriller","Christopher Nolan","Two rival stage magicians destroy each other chasing the perfect trick.",8.5),
("Memento",2000,"Mystery|Thriller","Christopher Nolan","A man with short term memory loss hunts for his wife's killer using notes.",8.4),
("Arrival",2016,"Drama|Sci-Fi","Denis Villeneuve","A linguist tries to communicate with mysterious alien visitors before war breaks out.",7.9),
("Dune",2021,"Adventure|Sci-Fi","Denis Villeneuve","A noble heir takes on a deadly desert planet and the fight over its spice.",8.0),
("Blade Runner 2049",2017,"Drama|Sci-Fi|Thriller","Denis Villeneuve","A new replicant hunter uncovers a secret that could plunge society into chaos.",8.0),
("The Truman Show",1998,"Comedy|Drama|Sci-Fi","Peter Weir","A man slowly realizes his whole life is a staged television show.",8.2),
("Eternal Sunshine of the Spotless Mind",2004,"Drama|Romance|Sci-Fi","Michel Gondry","After a bad breakup, a man has his memories of his partner erased.",8.3),
("A Beautiful Mind",2001,"Drama|Romance","Ron Howard","A brilliant mathematician struggles with mental illness while chasing his life's work.",8.2),
("Good Will Hunting",1997,"Drama|Romance","Gus Van Sant","A gifted janitor with a troubled past is helped by a therapist.",8.3),
("Rocky",1976,"Drama","John G. Avildsen","A small time boxer gets a shot at the heavyweight title.",8.1),
("Braveheart",1995,"Action|Drama|War","Mel Gibson","A Scottish warrior leads a rebellion against English rule.",8.3),
("Jaws",1975,"Adventure|Thriller","Steven Spielberg","A police chief, a scientist and a fisherman hunt a giant shark terrorizing a beach town.",8.1),
("E.T. the Extra-Terrestrial",1982,"Children|Drama|Sci-Fi","Steven Spielberg","A lonely boy befriends a stranded alien and helps him get home.",7.9),
("Ghostbusters",1984,"Action|Comedy|Sci-Fi","Ivan Reitman","Three scientists start a business catching ghosts in New York City.",7.8),
("The Exorcist",1973,"Horror","William Friedkin","Priests try to save a young girl possessed by a demon.",8.1),
("Get Out",2017,"Horror|Mystery|Thriller","Jordan Peele","A young man visiting his girlfriend's family discovers a disturbing secret.",7.7),
("A Quiet Place",2018,"Drama|Horror|Sci-Fi","John Krasinski","A family must live in silence to hide from deadly creatures that hunt by sound.",7.5),
("Halloween",1978,"Horror|Thriller","John Carpenter","A masked killer returns to his hometown to stalk babysitters on Halloween night.",7.7),
("The Shining",1980,"Horror","Stanley Kubrick","A writer and his family become winter caretakers of an isolated haunted hotel.",8.4),
("2001: A Space Odyssey",1968,"Adventure|Drama|Sci-Fi","Stanley Kubrick","Astronauts clash with a ship's computer on a mission tied to a mysterious monolith.",8.3),
("Gone Girl",2014,"Drama|Mystery|Thriller","David Fincher","A husband becomes the prime suspect when his wife disappears on their anniversary.",8.1),
("Knives Out",2019,"Comedy|Crime|Mystery","Rian Johnson","A detective investigates the death of a wealthy novelist surrounded by suspicious relatives.",7.9),
("The Good, the Bad and the Ugly",1966,"Western","Sergio Leone","Three gunslingers race to find buried Confederate gold during the Civil War.",8.8),
("Unforgiven",1992,"Drama|Western","Clint Eastwood","An aging gunman takes one last job and confronts his violent past.",8.2),
("Django Unchained",2012,"Action|Drama|Western","Quentin Tarantino","A freed slave and a bounty hunter set out to rescue his wife.",8.4),
("Free Solo",2018,"Documentary","Jimmy Chin and Elizabeth Chai Vasarhelyi","A climber attempts to scale a giant cliff without ropes or safety gear.",8.2),
]


def make_ratings(rng, n_users):
    genres = sorted({g for m in MOVIES for g in m[2].split("|")})
    rows = []
    for u in range(1, n_users + 1):
        fav = rng.sample(genres, rng.randint(2, 3))
        dis = rng.sample([g for g in genres if g not in fav], rng.randint(1, 2))
        aff = {g: rng.gauss(0, 0.25) for g in genres}
        for g in fav:
            aff[g] += 1.1 + rng.random() * 0.4
        for g in dis:
            aff[g] -= 1.0
        era = rng.choice([-1, 0, 1])  # -1 prefers old films, +1 prefers new ones
        for mid, (title, year, gs, _d, _o, acclaim) in enumerate(MOVIES, start=1):
            a = sum(aff[g] for g in gs.split("|")) / len(gs.split("|")) + 0.3 * era * (year - 1990) / 30
            watch_p = min(0.9, max(0.02, 0.07 + 0.05 * (acclaim - 6) + 0.22 * a))
            if rng.random() < watch_p:
                r = 3.2 + 0.45 * (acclaim - 7.8) + 1.0 * a + rng.gauss(0, 0.5)
                rows.append((u, mid, int(round(min(5, max(1, r))))))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=400)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="data")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "movies.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["movieId", "title", "genres", "director", "overview"])
        for i, (t, y, g, d, o, _) in enumerate(MOVIES, start=1):
            w.writerow([i, f"{t} ({y})", g, d, o])
    ratings = make_ratings(random.Random(a.seed), a.users)
    with open(os.path.join(a.out, "ratings.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["userId", "movieId", "rating"])
        w.writerows(ratings)
    print(f"Wrote {len(MOVIES)} movies and {len(ratings)} ratings from {a.users} users to {a.out}/")


if __name__ == "__main__":
    main()
