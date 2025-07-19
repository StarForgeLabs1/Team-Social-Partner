CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username TEXT NOT NULL,
  nickname TEXT,
  platform TEXT
);

CREATE TABLE accounts (
  id SERIAL PRIMARY KEY,
  username TEXT NOT NULL,
  platform TEXT
);

CREATE TABLE api_keys (
  id SERIAL PRIMARY KEY,
  name TEXT,
  value TEXT,
  user_id INTEGER REFERENCES users(id)
);

CREATE TABLE webhooks (
  id SERIAL PRIMARY KEY,
  url TEXT,
  user_id INTEGER REFERENCES users(id)
);

CREATE TABLE logs (
  id SERIAL PRIMARY KEY,
  message TEXT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);