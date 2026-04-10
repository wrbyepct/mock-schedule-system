from pwdlib import PasswordHash

pwd_hasher = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    return pwd_hasher.hash(plain_password)


def verify_password(plain_password: str, hash_password: str) -> bool:
    return pwd_hasher.verify(plain_password, hash_password)
