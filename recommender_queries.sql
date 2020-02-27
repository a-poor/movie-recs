-- 
-- NOTE: max year in dataset is 2016
-- 
-- Test User: 82665
-- Test Movie: 5773
-- 
-- score function:: score(n_reviews,avg_rating) = n_reviews * ln(avg_rating + 1)
--

-- Find the top 25 most rated movies
-- and their average ratings
SELECT 
    movies."movieId", 
    title, 
    c n_ratings, 
    avg_rating 
FROM 
    movies, 
    (SELECT 
        "movieId", 
        COUNT(*) c, 
        AVG(rating) avg_rating 
    FROM 
        ratings 
    GROUP BY 
        "movieId" 
    ORDER BY 
        c DESC 
    LIMIT 25) AS counts 
WHERE 
    movies."movieId" = counts."movieId";



-- Find the current most popular movies
-- time decay formula: (score - 1) / ((age + 2) ^ gravity)
SELECT 
    m."movieId",
    title,
    year,
--    poster_link,
--    plot_summary,
    (sc / (2017 - year)^5) score
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
LIMIT 40;


-- SELECT 
--     movie_votes."movieId", 
--     title, 
--     AVG(movie_votes.rating) avg_rating, 
--     COUNT(*) n_votes, ln(
--         ((AVG(movie_votes.rating)/ 5)+1) * COUNT(*)
--     ) score
-- FROM ratings movie_votes, movies
-- WHERE movie_votes."userId" <> 82665
--     AND movie_votes."movieId" = movies."movieId"
--     AND movie_votes.rating >= 3
--     AND movie_votes."userId" IN (
--         SELECT other_users."userId"
--         FROM ratings other_users 
--         WHERE other_users."userId" <> 82665 AND other_users."movieId" IN (
--             SELECT users_ratings."movieId"
--             FROM ratings users_ratings
--             WHERE users_ratings."userId" = 82665 AND users_ratings.rating >= 3
--         )
-- )
-- GROUP BY  movie_votes."movieId", title
-- ORDER BY avg_rating DESC
-- LIMIT 50;






-- Recommendations for you
-- Using `rating >= 3` as cuttoff
-- Sequence:
-- 1) Find movies you liked
-- 2) Find other people who liked those movies
-- 3) Find other movies those people liked
-- 4) Rank based on number of occurances / avg rating
-- 5) Filter out ones the user has already seen
-- 6) Take the top n suggestions

SELECT movieId FROM ratings WHERE userId = '<uid>' AND rating >= 3 ORDER BY rating DESC;

SELECT 
    movieId, 
    COUNT(*) n_votes
FROM 
    ratings
WHERE 
    userId <> '<uid>' 
    AND 
    rating >= 3
    AND
    userId IN (
        SELECT userId
        FROM ratings
        WHERE userId <> '<uid>' AND movieId IN (
            SELECT movieId
            FROM ratings
            WHERE userId = '<uid>' AND rating >= 3
        )
)
GROUP BY 
    movieId
ORDER BY
    n_votes DESC
LIMIT 
    <top n recs>;




-------------- TESTS ----------------------
SELECT "movieId" FROM ratings WHERE "userId" = 82665 AND rating >= 3 ORDER BY rating DESC;

SELECT  movie_votes."movieId", title, COUNT(*) n_votes
FROM ratings movie_votes, movies
WHERE movie_votes."userId" <> 82665
    AND movie_votes."movieId" = movies."movieId"
    AND movie_votes.rating >= 3
    AND movie_votes."userId" IN (
        SELECT other_users."userId"
        FROM ratings other_users 
        WHERE other_users."userId" <> 82665 AND other_users."movieId" IN (
            SELECT users_ratings."movieId"
            FROM ratings users_ratings
            WHERE users_ratings."userId" = 82665 AND users_ratings.rating >= 3
        )
)
GROUP BY  movie_votes."movieId", title
ORDER BY n_votes DESC
LIMIT 50;


SELECT movie_votes."movieId", title, AVG(movie_votes.rating) avg_rating, COUNT(*) n_votes
FROM ratings movie_votes, movies
WHERE movie_votes."userId" <> 82665
    AND movie_votes."movieId" = movies."movieId"
    AND movie_votes.rating >= 3
    AND movie_votes."userId" IN (
        SELECT other_users."userId"
        FROM ratings other_users 
        WHERE other_users."userId" <> 82665 AND other_users."movieId" IN (
            SELECT users_ratings."movieId"
            FROM ratings users_ratings
            WHERE users_ratings."userId" = 82665 AND users_ratings.rating >= 3
        )
)
GROUP BY  movie_votes."movieId", title
ORDER BY avg_rating DESC
LIMIT 50;


-- Get recommendations for the user
SELECT
    movie_final."movieId",
    movie_final.title,
    movie_final.year,
    -- movie_final.poster_link,
    -- movie_final.plot_summary,
    movie_picks.s2,
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
    WHERE movie_votes."userId" <> 82665
        AND year IS NOT NULL
        AND movie_votes."movieId" = movies."movieId"
        AND movie_votes.rating >= 3
        AND movie_votes."userId" IN (
            SELECT other_users."userId"
            FROM ratings other_users 
            WHERE other_users."userId" <> 82665 AND other_users."movieId" IN (
                SELECT users_ratings."movieId"
                FROM ratings users_ratings
                WHERE users_ratings."userId" = 82665 AND users_ratings.rating >= 3
            )
    )
    GROUP BY  movie_votes."movieId", title, movies.year
    ORDER BY score DESC
) movie_picks
WHERE
    movie_final."movieId" = movie_picks."movieId"
LIMIT 40;




-- Get movie info from movieId

SELECT 
    "movieId",
    title,
    year,
    poster_link,
    plot_summary
FROM movies
WHERE "movieId" = <mid>;




-- Get genres for a movie
SELECT genre 
FROM ml_genres 
WHERE "movieId" = <mid>;



-- Generate top 50 movie suggestions for the user

SELECT 
    movie_votes."movieId", 
    title, 
    AVG(movie_votes.rating) avg_rating, 
    COUNT(*) n_votes, ln(
        ((AVG(movie_votes.rating)/ 5)+1) * COUNT(*)
    ) score
FROM ratings movie_votes, movies
WHERE movie_votes."userId" <> 82665
    AND movie_votes."movieId" = movies."movieId"
    AND movie_votes.rating >= 3
    AND movie_votes."userId" IN (
        SELECT other_users."userId"
        FROM ratings other_users 
        WHERE other_users."userId" <> 82665 AND other_users."movieId" IN (
            SELECT users_ratings."movieId"
            FROM ratings users_ratings
            WHERE users_ratings."userId" = 82665 AND users_ratings.rating >= 3
        )
)
GROUP BY  movie_votes."movieId", title
ORDER BY avg_rating DESC
LIMIT 50;








-- def visualize(fn,n_reviews=None,ratings=None):
--     if n_reviews is None:
--         n_reviews = np.linspace(1,296800,100)
--     if ratings is None:
--         ratings = np.linspace(0.5,5,100)
--     scores = np.zeros((100,100))
--     for i in range(100):
--         for j in range(100):
--             scores[i,j] = fn(
--                 n_reviews[i],
--                 ratings[j]
--                 )
--     print("Min Score: %.3f" % scores.min())
--     print("Avg Score: %.3f" % scores.mean())
--     print("Max Score: %.3f" % scores.max())
--     sns.heatmap(
--         data=scores,
--         )
--     plt.xlabel("number of reviews")
--     xticks = np.linspace(n_reviews.min(),n_reviews.max(),10).astype('int32')
--     plt.xticks(np.arange(0,100,10),xticks)
--     plt.ylabel("rating score")
--     yticks = np.linspace(ratings.min(),ratings.max(),10).astype('int32')
--     plt.yticks(np.arange(0,100,10),yticks)
--     plt.show()
--     input("Press [return] to close... ")
--     plt.close()
--     return



-- User Id: 82665
-- Inside Out: 134853  |  32786862
-- Jungle Book: 137857 |    726161

--- Calculating the distance between movies
--- based on their nmf vectors


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
    WHERE a."movieId" = 134853 
        AND b."movieId" = 137857 
        AND a.nmf_category = b.nmf_category 
        AND a."movieId" <> b."movieId"
) AS d
GROUP BY mid_a, mid_b;


-- Find song distances
-- 1645
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
        WHERE "userId" = 82665
        ORDER BY rating DESC
        LIMIT 50
    )
        -- AND b."movieId" = 137857 
        AND a.nmf_category = b.nmf_category 
        AND a."movieId" <> b."movieId"
) AS d
GROUP BY mid_a, mid_b
ORDER BY dist
LIMIT 20;

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
            WHERE "userId" = 82665
            ORDER BY rating DESC
            LIMIT 50
        )
            -- AND b."movieId" = 137857 
            AND a.nmf_category = b.nmf_category 
            AND a."movieId" <> b."movieId"
    ) AS d
    GROUP BY mid_a, mid_b
    ORDER BY dist
    LIMIT 20
) as others
WHERE a."movieId" = others.mid_a
    AND b."movieId" = others.mid_b;

-- FROM: 750
-- TO:
-- 111848
-- 139616
-- 64983



-- Find the top movies for a user
SELECT "movieId", rating
FROM ratings
WHERE "userId" = 82665
ORDER BY rating DESC;





