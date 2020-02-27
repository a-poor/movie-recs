
import json
import psycopg2

class Recommendation:
    def __init__(self):
        self.db = psycopg2.connect("dbname=movies user=postgres password=metis")
        return

    def get_nonpersonalized(self,limit=50,time_decay_factor=5):
        c = self.db.cursor()
        c.execute("""
            SELECT 
                m."movieId",
                title,
                year,
                poster_link,
                plot_summary,
                (sc / (2017 - year)^%s) score
            FROM movies m, (
                SELECT 
                    r."movieId",
                    (COUNT(*) * ln(AVG(rating) + 1)) sc
                FROM ratings r
                GROUP BY r."movieId"
            ) AS s
            WHERE m."movieId" = s."movieId"
                AND year IS NOT NULL
            ORDER BY score DESC
            LIMIT %s;
        """, (
            time_decay_factor,
            limit
        ))
        return

    def get_semipersonalized(self,uid):
        c = self.db.cursor()
        c.execute("""

        """)
        return

    def get_personalized_collab(self,uid,limit=50):
        c = self.db.cursor()
        c.execute("""
            SELECT
                movie_final."movieId",
                movie_final.title,
                movie_final.year,
                movie_final.poster_link,
                movie_final.plot_summary,
                movie_picks.score
            FROM movies movie_final, (
                SELECT 
                    movie_votes."movieId", 
                    title, 
                    AVG(movie_votes.rating) avg_rating, 
                    COUNT(*) n_votes, 
                    (COUNT(*) * ln(AVG(movie_votes.rating) + 1)) s2,
                    (COUNT(*) * ln(AVG(movie_votes.rating) + 1) / (2017 - movies.year) ^2 ) score
                FROM ratings movie_votes, movies
                WHERE movie_votes."userId" <> %s
                    AND year IS NOT NULL
                    AND movie_votes."movieId" = movies."movieId"
                    AND movie_votes.rating >= 3
                    AND movie_votes."userId" IN (
                        SELECT other_users."userId"
                        FROM ratings other_users 
                        WHERE other_users."userId" <> %s AND other_users."movieId" IN (
                            SELECT users_ratings."movieId"
                            FROM ratings users_ratings
                            WHERE users_ratings."userId" = %s AND users_ratings.rating >= 3
                        )
                )
                GROUP BY  movie_votes."movieId", title, movies.year
                ORDER BY score DESC
            ) movie_picks
            WHERE
                movie_final."movieId" = movie_picks."movieId"
            LIMIT %s;
        """, (
            uid,uid,uid,
            limit
        ))
        return c.fetchall()
    
    def get_personalized_content(self,uid,movie_seed_limit=50,movie_rec_limit=20):
        c = self.db.cursor()
        c.execute("""
            SELECT 
                a.title,
                a.year,
                b.title,
                b.year,
                b.poster_link,
                b.plot_summary
            FROM movies a, movies b, (
                SELECT mid_a, mid_b, SUM(sq_diff)^0.5 dist
                FROM (
                    SELECT 
                        a."movieId" mid_a, 
                        b."movieId" mid_b, 
                        a.nmf_category cat, 
                        (a.nmf_vector - b.nmf_vector)^2 sq_diff 
                    FROM 
                        nmf_vectors a, 
                        nmf_vectors b 
                    WHERE a."movieId" IN (
                        SELECT "movieId"
                        FROM ratings
                        WHERE "userId" = %s
                        ORDER BY rating DESC
                        LIMIT %s
                    )
                        AND a.nmf_category = b.nmf_category 
                        AND a."movieId" <> b."movieId"
                ) AS d
                GROUP BY mid_a, mid_b
                ORDER BY dist
                LIMIT %s
            ) as others
            WHERE a."movidId" = others.mid_a
                AND b."movidId" = others.mid_b;
        """, (
            uid,
            movie_seed_limit,
            movie_rec_limit
        ))
        return c.fetchall()
