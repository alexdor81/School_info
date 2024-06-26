CREATE OR REPLACE FUNCTION fnc_transferredpoints()
    RETURNS TABLE("Peer1" VARCHAR,
    "Peer2" VARCHAR,
    "PointsAmount" BIGINT) AS $$
    SELECT "TransferredPoints"."CheckingPeer", "TransferredPoints"."CheckedPeer",
           ("TransferredPoints"."PointsAmount" - cte_1."PointsAmount")
    FROM "TransferredPoints" JOIN "TransferredPoints" AS cte_1
    ON "TransferredPoints"."CheckingPeer" = cte_1."CheckedPeer" AND
       "TransferredPoints"."CheckedPeer" = cte_1."CheckingPeer"
    ORDER BY 1, 2;
    $$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION  fnc_xp()
    RETURNS TABLE("Peer" VARCHAR,
                  "Task" VARCHAR,
                  "XP" BIGINT) AS $$
    SELECT "Nickname", "Title", "XPAmount"
    FROM "Peers"
         INNER JOIN "Checks" ON "Peers"."Nickname" = "Checks"."Peer"
         INNER JOIN "Tasks" ON "Checks"."Task" = "Tasks"."Title"
         INNER JOIN "XP" ON "Checks"."id" = "XP"."Check"
    ORDER BY 1,2;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION fnc_not_left_campus(check_date character) RETURNS TABLE(
    "Peer" VARCHAR) AS $$
    SELECT "Peer" FROM "TimeTracking"
    WHERE "Date" = to_date(check_date, 'DD.MM.YYYY')
    GROUP BY "Peer"
    HAVING COUNT("State") = 2
    $$ LANGUAGE SQL;

CREATE OR REPLACE PROCEDURE pr_success_checks(IN result REFCURSOR = 'procedure_result')
LANGUAGE plpgsql AS $$
    BEGIN
     OPEN result FOR
        SELECT ROUND((SELECT COUNT(*) FROM "XP")/(SELECT COUNT(*) FROM "Checks")::NUMERIC * 100, 0)
        AS "SuccessfulChecks",
            ROUND(((SELECT COUNT(*) FROM "Checks") - (SELECT COUNT(*) FROM "XP")) /
                  (SELECT COUNT(*) FROM "Checks")::NUMERIC * 100, 0)
        AS "UnsuccessfulChecks";
    END;
    $$;

CREATE OR REPLACE PROCEDURE pr_points_change_1(IN result REFCURSOR = 'procedure_result')
LANGUAGE plpgsql AS $$
    BEGIN
        OPEN result FOR
        WITH get_points AS (SELECT "CheckingPeer", SUM("PointsAmount") AS total
                            FROM "TransferredPoints"
                            GROUP BY "CheckingPeer" ),
            give_points AS (SELECT "CheckedPeer", SUM("PointsAmount") AS total
                            FROM "TransferredPoints"
                            GROUP BY "CheckedPeer" )
        SELECT "CheckingPeer" AS "Peer",
           (get_points.total - give_points.total) AS "PointsChange"
        FROM get_points JOIN give_points
            ON get_points."CheckingPeer" = give_points."CheckedPeer"
        ORDER BY 2 DESC ;
    END;
    $$;

CREATE OR REPLACE PROCEDURE pr_points_change_2(IN result REFCURSOR = 'procedure_result')
LANGUAGE plpgsql AS $$
    BEGIN
        OPEN result FOR
            SELECT "Peer1", SUM("PointsAmount")
            FROM fnc_transferredpoints()
            GROUP BY "Peer1"
            ORDER BY 2 DESC;
    END;
    $$;

CREATE OR REPLACE PROCEDURE pr_frequently_checked(IN result REFCURSOR = 'procedure_result')
LANGUAGE plpgsql AS $$
BEGIN
    OPEN result FOR
    SELECT "Date", "Task"
    FROM (
        SELECT "Date", "Task",
               RANK() OVER (PARTITION BY "Date" ORDER BY COUNT("Task") DESC ) AS rating
        FROM "Checks"
        GROUP BY "Date", "Task") query_1
    WHERE rating = 1
    ORDER BY 1 DESC ;
END;
$$;

CREATE OR REPLACE PROCEDURE pr_duration_last_check(IN result REFCURSOR = 'procedure_result')
    LANGUAGE plpgsql AS $$
BEGIN
    OPEN result FOR
        WITH cte_last_p2p AS (SELECT "P2P"."Check"
                        FROM "Checks"
                        INNER JOIN "P2P" ON "Checks"."id" = "P2P"."Check"
                        ORDER BY "Date" DESC, "Time" DESC
                        LIMIT 1)
    SELECT ((SELECT "P2P"."Time" FROM "P2P" JOIN cte_last_p2p
            ON "P2P"."Check" = cte_last_p2p."Check"
             WHERE "State" != 'Start') -
            (SELECT "P2P"."Time" FROM "P2P" JOIN cte_last_p2p
            ON "P2P"."Check" = cte_last_p2p."Check"
            WHERE "State" = 'Start'))::time AS delta_time;
END;
$$;

CREATE OR REPLACE PROCEDURE pr_completed_block(block varchar, IN curs refcursor = 'procedure_result') AS
$$
BEGIN
    OPEN curs FOR WITH success_check AS (SELECT "Checks".id, "Peer", "Task", "Date"
                                        FROM "Checks"
                                        JOIN "P2P" ON "Checks".id = "P2P"."Check" AND "P2P"."State" = 'Success'
                                        WHERE "Checks".id NOT IN (SELECT "Check"
                                        FROM "Verter"
                                        WHERE "State" = 'Start'
                                        EXCEPT
                                        SELECT "Check"
                                        FROM "Verter"
                                        WHERE "State" = 'Success')), 
                    cte AS (SELECT MAX("Title") AS task
                               FROM "Tasks"
                               WHERE "Title" IN
                                     (SELECT UNNEST(REGEXP_MATCHES("Title", CONCAT('(', block, '\d.*)'))) FROM "Tasks"))
                    SELECT "Peer", "Date" AS day
                    FROM success_check
                           JOIN cte ON success_check."Task" = cte.task
                    ORDER BY day;
END
$$ LANGUAGE plpgsql;


CREATE OR REPLACE PROCEDURE pr_recommended(IN result REFCURSOR = 'procedure_result')
    LANGUAGE plpgsql AS $$
BEGIN
    OPEN result FOR
        WITH cte_recommended AS (
            WITH cte_tmp AS (SELECT DISTINCT "Nickname", "Peer2", "RecommendedPeer",
                    COUNT("RecommendedPeer") OVER (PARTITION BY "Nickname", "RecommendedPeer")  AS rating
            FROM "Peers"
            INNER JOIN "Friends" ON "Peers"."Nickname" = "Friends"."Peer1"
            INNER JOIN "Recommendations" ON "Recommendations"."Peer" = "Friends"."Peer2" AND
         "Peers"."Nickname" != "Recommendations"."RecommendedPeer")
       SELECT "Nickname", "RecommendedPeer", cte_tmp.rating,
           ROW_NUMBER() OVER (PARTITION BY "Nickname" ORDER BY cte_tmp.rating DESC ) AS rating_value
           FROM cte_tmp)
    SELECT "Nickname", "RecommendedPeer"
    FROM cte_recommended
    WHERE rating_value = 1;
END;
$$;

CREATE OR REPLACE PROCEDURE pr_percentage(block_1 VARCHAR, block_2 VARCHAR,
    IN result REFCURSOR = 'procedure_result')
    LANGUAGE plpgsql AS $$
BEGIN
    OPEN result FOR
        WITH cte_peer_block AS (SELECT DISTINCT "Peer", CASE
                                            WHEN "Task" LIKE 'CPP_\_%' THEN 'CPP'
                                            WHEN "Task" LIKE 'C_\_%'  THEN 'C'
                                            WHEN "Task" LIKE 'DO_\_%' THEN 'DO'
                                            WHEN "Task" LIKE 'A_\_%' THEN 'A'
                                            WHEN "Task" LIKE 'SQL_\_%' THEN 'SQL'
                                            ELSE ''
                                        END AS block_project
                                FROM "Checks" ),
            cte_block_1 AS (SELECT COUNT(block_project) AS count_block_1, 1 AS id_value
                            FROM cte_peer_block
                            WHERE block_project != '' AND block_project = block_1
                            GROUP BY block_project),
            cte_block_2 AS (SELECT COUNT(block_project) AS count_block_2, 1 AS id_value
                            FROM cte_peer_block
                            WHERE block_project != '' AND block_project = block_2
                            GROUP BY block_project),
            cte_both AS (SELECT COUNT(DISTINCT "Peer") AS count_bouth, 1 AS id_value
                        FROM cte_peer_block
                        WHERE block_project != '' AND (block_project = block_1 OR block_project = block_2)),
            cte_peers AS (SELECT COUNT("Nickname") AS count_all, 1 AS id_value
                          FROM "Peers")
    SELECT ROUND((cte_block_1.count_block_1 / cte_peers.count_all::NUMERIC) * 100, 0) AS "StartedBlock1",
    ROUND((cte_block_2.count_block_2 / cte_peers.count_all::NUMERIC) * 100, 0) AS "StartedBlock2",
    ROUND((cte_both.count_bouth / cte_peers.count_all::NUMERIC) * 100, 0) AS "StartedBothBlocks",
    ROUND((cte_peers.count_all - cte_both.count_bouth) / cte_peers.count_all::NUMERIC * 100, 0) AS "DidntStartAnyBlock"
    FROM cte_block_1
        INNER JOIN  cte_block_2 ON cte_block_1.id_value = cte_block_2.id_value
        INNER JOIN  cte_peers ON cte_peers.id_value = cte_block_2.id_value
        INNER JOIN cte_both ON cte_both.id_value = cte_peers.id_value;
    END;
$$;

CREATE OR REPLACE PROCEDURE pr_friendscount( limit_value INT,
    IN result REFCURSOR = 'procedure_result')
    LANGUAGE plpgsql AS $$
BEGIN
    OPEN result FOR
        SELECT "Nickname" AS "Peer", COUNT("Peer2") AS "FriendsCount"
        FROM "Peers"
        INNER JOIN "Friends" ON "Peers"."Nickname" = "Friends"."Peer1"
        GROUP BY "Nickname"
        ORDER BY 2 DESC
        LIMIT limit_value;
END;
$$;

CREATE OR REPLACE PROCEDURE pr_birthday_success(IN result REFCURSOR = 'procedure_result')
    LANGUAGE plpgsql AS $$
BEGIN
    OPEN result FOR
        WITH cte_find_dates AS (SELECT "Nickname",
                CONCAT(DATE_PART('day', "Birthday"), '_', DATE_PART('month', "Birthday")) AS "Birthday",
                CONCAT(DATE_PART('day', "Date"), '_', DATE_PART('month', "Date")) AS "Date",
                "P2P"."State" AS p2p_state, "Verter"."State" AS verter_state
                  FROM "Peers" INNER JOIN "Checks" ON "Peers"."Nickname" = "Checks"."Peer"
                      INNER JOIN "P2P" ON "Checks"."id" = "P2P"."Check"
                      LEFT JOIN "Verter" ON "Checks"."id" = "Verter"."Check"),
            cte_success AS (SELECT COUNT("Nickname") AS count_peers, 1 AS id_value
                            FROM cte_find_dates
                            WHERE "Birthday" = "Date" AND (p2p_state = 'Success' OR verter_state = 'Success')),
            cte_failure AS (SELECT COUNT("Nickname") AS count_peers, 1 AS id_value
                            FROM cte_find_dates
                            WHERE "Birthday" = "Date" AND (p2p_state = 'Failure' OR verter_state = 'Failure')),
            cte_all AS (SELECT COUNT("Nickname") AS count_peers, 1 AS id_value FROM "Peers")
    SELECT ROUND((cte_success.count_peers / cte_all.count_peers::NUMERIC) * 100, 0) AS "SuccessfulChecks",
            ROUND((cte_failure.count_peers / cte_all.count_peers::NUMERIC) * 100, 0) AS "UnsuccessfulChecks"
    FROM cte_success
        INNER JOIN cte_failure ON cte_success.id_value = cte_failure.id_value
        INNER JOIN cte_all ON cte_failure.id_value = cte_all.id_value;
END;
$$;

CREATE OR REPLACE PROCEDURE pr_max_xp(IN result REFCURSOR = 'procedure_result')
    LANGUAGE plpgsql AS $$
BEGIN
    OPEN result FOR
        SELECT "Nickname" AS "Peer", SUM("XPAmount") AS "XP"
        FROM (SELECT "Nickname", "Task", "XPAmount",
            ROW_NUMBER() OVER (PARTITION BY "Task", "Nickname" ORDER BY "Task" DESC ) AS rating
              FROM "Checks" INNER JOIN "XP" ON "Checks"."id" = "XP"."Check"
                  INNER JOIN "Peers" ON "Checks"."Peer" = "Peers"."Nickname") query_xp
        WHERE rating = 1
        GROUP BY "Nickname"
        ORDER BY 2;
END;
$$;

CREATE OR REPLACE PROCEDURE pr_tasks_1_2_3(task_1 VARCHAR, task_2 VARCHAR, task_3 VARCHAR, IN result REFCURSOR = 'procedure_result')
    LANGUAGE plpgsql AS
$$
BEGIN
    OPEN result FOR WITH success_check AS (SELECT "Checks".id, "Peer", "Task", "Date"
                                        FROM "Checks"
                                        JOIN "P2P" ON "Checks".id = "P2P"."Check" AND "P2P"."State" = 'Success'
                                        WHERE "Checks".id NOT IN (SELECT "Check"
                                        FROM "Verter"
                                        WHERE "State" = 'Start'
                                        EXCEPT
                                        SELECT "Check"
                                        FROM "Verter"
                                        WHERE "State" = 'Success'))
                (SELECT "Peer"
                FROM success_check
                WHERE "Task" = task_1
                INTERSECT
                SELECT "Peer"
                FROM success_check
                WHERE "Task" = task_2)
                EXCEPT
                SELECT "Peer"
                FROM success_check
                WHERE "Task" = task_3;
END
$$;

CREATE OR REPLACE PROCEDURE pr_prevcount(IN result REFCURSOR = 'procedure_result')
    LANGUAGE plpgsql AS $$
BEGIN
    OPEN result FOR
          WITH RECURSIVE amount AS (SELECT "Title", "ParentTask", 0 AS cost
                                      FROM "Tasks"
                                     UNION
          (SELECT ts."Title", ts."ParentTask", amount.cost + 1
             FROM "Tasks" ts
                      JOIN amount ON ts."ParentTask" = amount."Title"
            WHERE ts."ParentTask" IS NOT NULL))

        SELECT "Title" AS Task, MAX(cost) AS PrevCount
          FROM amount
         GROUP BY "Title"
         ORDER BY PrevCount;
END
$$;

CREATE OR REPLACE PROCEDURE pr_count_lucky_days(count_success INT, IN result REFCURSOR = 'procedure_result'
) LANGUAGE plpgsql AS $$
    BEGIN
        OPEN result FOR
            WITH cte_lucky AS (
                    SELECT "Date", "Checks"."id", "P2P"."Time", "State", 'check_2_p2p' AS type, "MaxXP"
                    FROM "P2P" INNER JOIN "Checks" ON "P2P"."Check" = "Checks"."id"
                        INNER JOIN "Tasks" ON "Checks"."Task" = "Tasks"."Title"
                    UNION
                    SELECT "Date", "Checks"."id", "Verter"."Time", "State", 'check_1_verter' AS type, "MaxXP"
                    FROM "Verter" INNER JOIN "Checks" ON "Verter"."Check" = "Checks"."id"
                        INNER JOIN "Tasks" ON "Checks"."Task" = "Tasks"."Title" ),
                query_lucky AS (
                    SELECT "Date", "id", "Time", "State", type, "MaxXP",
                           ROW_NUMBER() OVER (PARTITION BY "Date", cte_lucky."id" ORDER BY type, "State" DESC) as rating
                    FROM cte_lucky),
                query_final AS (
                    SELECT CASE
                        WHEN COALESCE(ROUND(("XPAmount" / "MaxXP"::NUMERIC) * 100, 0), 0) >= 80
                        THEN "State"
                        ELSE 'Failure' END AS State_value,
                        type, "Date", query_lucky."id", "Time",
                                   COALESCE(ROUND(("XPAmount" / "MaxXP"::NUMERIC) * 100, 0), 0) AS count_xp
                    FROM query_lucky LEFT JOIN "XP" ON "XP"."Check" = query_lucky."id"
                    WHERE rating = 1
                )
        SELECT DISTINCT "Date"
        FROM (
        SELECT "Date", query_final."id", "Time", State_value, type, count_xp,
               ROW_NUMBER() OVER (PARTITION BY "Date", State_value ORDER BY "Date", "Time", "id") AS rating_fail,
               ROW_NUMBER() OVER (PARTITION BY "Date" ORDER BY "Date", "Time", "id") AS rating_query
        FROM query_final
        ORDER BY 1, 3) query_common
        WHERE rating_fail = rating_query AND State_value != 'Failure' AND rating_query = count_success;
    END;
    $$;

CREATE OR REPLACE PROCEDURE pr_peer_max_count_task(IN result REFCURSOR = 'procedure_result')
    LANGUAGE plpgsql AS $$
    BEGIN
       OPEN result FOR
        WITH max_count AS (SELECT COUNT("XPAmount")
                           FROM "XP" JOIN "Checks" ON "XP"."Check" = "Checks"."id"
                               JOIN "Peers" ON "Checks"."Peer" = "Peers"."Nickname"
                           GROUP BY "Peer"
                           ORDER BY 1 DESC
                           LIMIT 1)
        SELECT "Peer", COUNT("XPAmount") AS "Completed"
        FROM "XP" JOIN "Checks" ON "XP"."Check" = "Checks"."id"
            JOIN "Peers" ON "Checks"."Peer" = "Peers"."Nickname"
        GROUP BY "Peer"
        HAVING COUNT("XPAmount") = (SELECT * FROM max_count);
       END
    $$;

CREATE OR REPLACE PROCEDURE pr_peer_max_xp(IN result REFCURSOR = 'procedure_result')
    LANGUAGE plpgsql AS $$
    BEGIN
       OPEN result FOR
        WITH max_xp AS (SELECT SUM("XPAmount")
                        FROM "XP" JOIN "Checks" ON "XP"."Check" = "Checks"."id"
                            JOIN "Peers" ON "Checks"."Peer" = "Peers"."Nickname"
                        GROUP BY "Peer"
                        ORDER BY 1 DESC
                        LIMIT 1)
        SELECT "Peer", SUM("XPAmount") AS "XP"
        FROM "XP" JOIN "Checks" ON "XP"."Check" = "Checks"."id"
            JOIN "Peers" ON "Checks"."Peer" = "Peers"."Nickname"
        GROUP BY "Peer"
        HAVING SUM("XPAmount") = (SELECT * FROM max_xp);
       END
    $$;

CREATE OR REPLACE PROCEDURE pr_peer_max_time_today(IN result REFCURSOR = 'procedure_result')
    LANGUAGE plpgsql AS $$
    BEGIN
       OPEN result FOR
       WITH time_arrive AS (SELECT ROW_NUMBER() OVER () AS id,  "Peer", "Time" as arrive
                            FROM "TimeTracking"
                            WHERE "Date" = current_date AND "State" = 1
                            ORDER BY 1, 2),
           time_departure AS (SELECT ROW_NUMBER() OVER () AS id,  "Peer", "Time" as departure
                            FROM "TimeTracking"
                            WHERE "Date" = current_date AND "State" = 2
                            ORDER BY 1, 2),
           time_by_peer AS (SELECT time_arrive."Peer" AS Peer,
                                   SUM(departure - arrive)::time AS campus_time
                            FROM time_arrive JOIN time_departure
                                ON time_arrive.id = time_departure.id
                            GROUP BY time_arrive."Peer")
       SELECT Peer FROM time_by_peer
       WHERE campus_time =
        (SELECT MAX(campus_time) FROM time_by_peer);
       END;
    $$;

CREATE OR REPLACE PROCEDURE pr_peer_come_ealier(time_arrive time, number int, IN result REFCURSOR)
    LANGUAGE plpgsql
AS $$
    BEGIN
       OPEN result FOR
        SELECT "Peer" FROM "TimeTracking"
        WHERE "State" = 1 AND "Time" < time_arrive
        GROUP BY "Peer"
        HAVING COUNT("Peer") >= number
       ORDER BY 1;
       END;
    $$;

CREATE OR REPLACE PROCEDURE pr_peer_leave(days int, number int, IN result REFCURSOR)
    LANGUAGE plpgsql
AS $$
    BEGIN
       OPEN result FOR
        SELECT "Peer" FROM "TimeTracking"
        WHERE "State" = 2 AND "Date" >= (current_date - days)
        GROUP BY "Peer"
        HAVING COUNT("Peer") > number
       ORDER BY 1;
       END;
    $$;

CREATE OR REPLACE PROCEDURE pr_peer_the_last_arrive_today(IN result REFCURSOR = 'procedure_result')
    LANGUAGE plpgsql AS $$
    BEGIN
       OPEN result FOR
        WITH latiest_time AS (SELECT MAX("Time")
                              FROM "TimeTracking"
                               WHERE "State" = 1 AND "Date" = current_date
        )
        SELECT "Peer" FROM "TimeTracking"
        WHERE "State" = 1 AND "Time" =
                              (SELECT * FROM latiest_time);
       END;
    $$;

CREATE OR REPLACE PROCEDURE pr_peer_absent_yesterday(time_absent interval MINUTE, IN result REFCURSOR)
    LANGUAGE plpgsql AS $$
    BEGIN
       OPEN result FOR
       WITH time_arrive AS (SELECT ROW_NUMBER() OVER () AS id,  "Peer", "Time" as arrive
                            FROM "TimeTracking"
                            WHERE "Date" = current_date - 1 AND "State" = 1
                            ORDER BY 1, 2),
           time_departure AS (SELECT ROW_NUMBER() OVER () AS id,  "Peer", "Time" as departure
                            FROM "TimeTracking"
                            WHERE "Date" = current_date - 1 AND "State" = 2
                            ORDER BY 1, 2),
           time_by_peer AS (SELECT time_arrive."Peer" AS Peer,
                                   SUM(departure - arrive)::time AS campus_time
                            FROM time_arrive JOIN time_departure
                                ON time_arrive.id = time_departure.id
                            GROUP BY time_arrive."Peer"),
           total_time_by_peer AS (SELECT time_arrive."Peer" AS Peer,
                                   (MAX(departure) - MIN(arrive))::time AS campus_time
                            FROM time_arrive JOIN time_departure
                                ON time_arrive.id = time_departure.id
                            GROUP BY time_arrive."Peer")
        SELECT time_by_peer.Peer AS "Peers"
        FROM time_by_peer JOIN total_time_by_peer USING(Peer)
        WHERE (total_time_by_peer.campus_time - time_by_peer.campus_time) > time_absent;
       END;
    $$;

CREATE OR REPLACE PROCEDURE pr_early_entries(IN result REFCURSOR) AS $$
    BEGIN
        OPEN result FOR
            WITH cte_peer_come AS (
                SELECT count(*) AS count1, to_char("Birthday", 'Month') AS "Month"
                FROM "Peers" INNER JOIN "TimeTracking" ON "Peers"."Nickname" = "TimeTracking"."Peer"
                WHERE to_char("Birthday", 'Month') = to_char("Date", 'Month') AND "State" = 1
                GROUP BY "Birthday"),
                cte_peer_come_before AS (
                SELECT count(*) AS count2, to_char("Birthday", 'Month') AS "Month"
                FROM "Peers" INNER JOIN "TimeTracking" ON "Peers"."Nickname" = "TimeTracking"."Peer"
                WHERE to_char("Birthday", 'Month') = to_char("Date", 'Month') AND "State" = 1 AND "Time" < '12:00:00'
                GROUP BY "Birthday")
        SELECT cte_peer_come."Month",
            CASE WHEN count2 IS NULL THEN 0
                ELSE round(count2 / count1::DECIMAL * 100)
            END AS "EarlyEntries"
        FROM cte_peer_come
            LEFT JOIN cte_peer_come_before ON cte_peer_come."Month" = cte_peer_come_before."Month"
        ORDER BY 1;
    END;
    $$ LANGUAGE plpgsql;
