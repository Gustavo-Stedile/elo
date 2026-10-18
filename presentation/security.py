from datetime import datetime, timedelta, timezone
import jwt

# TIRAR ISSO DAQUI EM PRODUCAO
SECRET_KEY = "0398YU108TH0FN341208NF028N208V4N"
ALGORITHM = "HS256"
ACESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    data_to_encode = data.copy()
    expire_date = datetime.now(timezone.utc) + \
        timedelta(minutes=ACESS_TOKEN_EXPIRE_MINUTES)

    data_to_encode.update({"exp": expire_date})
    return jwt.encode(data_to_encode, SECRET_KEY, algorithm=ALGORITHM)

