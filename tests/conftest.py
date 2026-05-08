"""Pytest config: clear chat-backend env vars before any app import."""
import os

os.environ.setdefault("FOUNDRY_PROJECT_ENDPOINT", "")
os.environ.setdefault("CS_DIRECTLINE_TOKEN_ENDPOINT", "")
os.environ.setdefault("LOG_LEVEL", "WARNING")
