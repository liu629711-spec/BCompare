-- user table setup (v2)
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

INSERT INTO users VALUES (1, 'Alice');
