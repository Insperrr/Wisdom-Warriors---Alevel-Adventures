CREATE TABLE User (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    time_created TIMESTAMP NOT NULL
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE Characters (
    character_id INTEGER PRIMARY KEY,
    character_name TEXT NOT NULL UNIQUE,
    character_description TEXT NOT NULL
);
CREATE TABLE Enemies (
    enemy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    enemy_name TEXT NOT NULL UNIQUE
);
CREATE TABLE Subject (
    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL,
    subject_info TEXT NOT NULL
);
CREATE TABLE EnemiesKilled (
    enemy_killed_id INTEGER PRIMARY KEY AUTOINCREMENT,
    enemy_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    FOREIGN KEY(enemy_id) REFERENCES Enemies(enemy_id),
    FOREIGN KEY(character_id) REFERENCES Characters(character_id),
    FOREIGN KEY(user_id) REFERENCES User(user_id)
);
CREATE TABLE Questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    "question_text" TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    option_1 TEXT NOT NULL,
    option_2 TEXT NOT NULL,
    option_3 TEXT NOT NULL,
    UNIQUE("question_text"),
    FOREIGN KEY(topic_id) REFERENCES Topic(topic_id),
    FOREIGN KEY(subject_id) REFERENCES Subject(subject_id)
);
CREATE TABLE Topic (
    topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    "topic_text" TEXT NOT NULL,
    FOREIGN KEY(subject_id) REFERENCES Subject(subject_id)
);
CREATE TABLE IF NOT EXISTS "HighScore" (
    high_score_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL, topic_id INTEGER NOT NULL REFERENCES Topic(topic_id),
    high_score INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES User(user_id),
    FOREIGN KEY(character_id) REFERENCES Characters(character_id),
    FOREIGN KEY(subject_id) REFERENCES Subject(subject_id)
);
