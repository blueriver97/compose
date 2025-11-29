DELIMITER $$
DROP EVENT IF EXISTS insert_lower_every_sec;
CREATE EVENT insert_lower_every_sec
    ON SCHEDULE EVERY 5 SECOND
    DO
    BEGIN
        SET @key = LOWER(CONCAT(
                HEX(RANDOM_BYTES(4)),
                '-', HEX(RANDOM_BYTES(2)),
                '-4', SUBSTR(HEX(RANDOM_BYTES(2)), 2, 3),
                '-', HEX(FLOOR(ASCII(RANDOM_BYTES(1)) / 64) + 8), SUBSTR(HEX(RANDOM_BYTES(2)), 2, 3),
                '-', HEX(RANDOM_BYTES(6))
            ));
        INSERT INTO tb_lower (id, char36, varchar36, integer1, integer2, unsigned_int, float1, double1, boolean1, text1, date1)
        VALUES (NULL, @`key`, @`key`, 1, 2147483647 + 1, 4294967295 - 1, 12.34, 1234.5678, TRUE, @`key`, CURRENT_DATE);
    END $$
DELIMITER ;

DELIMITER $$
DROP EVENT IF EXISTS update_lower_every_sec;
CREATE EVENT update_lower_every_sec
    ON SCHEDULE EVERY 7 SECOND
    DO
    BEGIN
        SELECT COUNT(1)
        INTO @cnt
        FROM tb_lower;
        SELECT RAND() * (@cnt + 1) INTO @target_id;
        UPDATE tb_lower
        SET integer1 = integer1 + 1
        WHERE id = FLOOR(@target_id);
    END $$
DELIMITER ;

DELIMITER $$
DROP EVENT IF EXISTS insert_upper_every_sec;
CREATE EVENT insert_upper_every_sec
    ON SCHEDULE EVERY 5 SECOND
    DO
    BEGIN
        SET @key = LOWER(CONCAT(
                HEX(RANDOM_BYTES(4)),
                '-', HEX(RANDOM_BYTES(2)),
                '-4', SUBSTR(HEX(RANDOM_BYTES(2)), 2, 3),
                '-', HEX(FLOOR(ASCII(RANDOM_BYTES(1)) / 64) + 8), SUBSTR(HEX(RANDOM_BYTES(2)), 2, 3),
                '-', HEX(RANDOM_BYTES(6))
            ));
        INSERT INTO TB_UPPER (ID, CHAR36, VARCHAR36, INTEGER1, INTEGER2, UNSIGNED_INT, FLOAT1, DOUBLE1, BOOLEAN1, TEXT1, DATE1)
        VALUES (NULL, @`key`, @`key`, 1, 2147483647 + 1, 4294967295 - 1, 12.34, 1234.5678, TRUE, @`key`, CURRENT_DATE);
    END $$
DELIMITER ;

DELIMITER $$
DROP EVENT IF EXISTS update_upper_every_sec;
CREATE EVENT update_upper_every_sec
    ON SCHEDULE EVERY 11 SECOND
    DO
    BEGIN
        SELECT COUNT(1)
        INTO @cnt
        FROM TB_UPPER;
        SELECT RAND() * (@cnt + 1) INTO @target_id;
        UPDATE TB_UPPER
        SET INTEGER1 = INTEGER1 + 1
        WHERE ID = FLOOR(@target_id);
    END $$
DELIMITER ;
