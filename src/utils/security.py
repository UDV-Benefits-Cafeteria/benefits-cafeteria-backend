from passlib.context import CryptContext

# Create a CryptContext for password hashing using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plaintext password.

    This function takes a plaintext password and returns a hashed version
    of it using bcrypt. The hashing is done with a context that
    automatically handles salting and strength parameters.

    Args:
        password (str): The plaintext password to be hashed.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a hashed password.

    This function checks whether the provided plaintext password matches
    the given hashed password. It uses bcrypt for verification.

    Args:
        plain_password (str): The plaintext password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the plaintext password matches the hashed password,
              False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)
