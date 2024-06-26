CREATE DATABASE info21_db;
CREATE USER student WITH ENCRYPTED PASSWORD 'student';
ALTER ROLE student SET client_encoding TO 'utf8';
ALTER ROLE student SET default_transaction_isolation TO 'read committed';
ALTER ROLE student SET timezone TO 'UTC';
ALTER DATABASE info21_db OWNER TO student;
GRANT ALL PRIVILEGES ON DATABASE info21_db TO student;
