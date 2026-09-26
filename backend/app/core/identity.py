"""Canonical identity keys shared by registration, login and admin operations."""


def normalize_email(email: str) -> str:
    return email.strip().lower()
