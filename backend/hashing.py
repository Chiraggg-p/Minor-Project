# hashing.py
# This file handles all our password security.

from passlib.context import CryptContext

# Using scrypt as the hashing scheme
pwd_context = CryptContext(schemes=["scrypt"], deprecated="auto")

class Hash():
    def get_password_hash(password: str):
        """
        Takes a plain-text password and returns a scrambled (hashed) version.
        """
        return pwd_context.hash(password)

    def verify_password(plain_password: str, hashed_password: str):
        """
        Checks if the plain password matches the scrambled one from our database.
        """
        return pwd_context.verify(plain_password, hashed_password)
