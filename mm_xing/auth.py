from httpx import Client

from mm_xing.constant import XING_AUTH_URL
from mm_xing.schemas import XingAuthHeaders, XingAuthParams


def get_access_token(
    client: Client, 
    app_key: str | None, 
    app_secret: str | None
):
    if not app_key or not app_secret:
        raise ValueError("app_key and app_secret must be provided")

    response = client.post(
        url=XING_AUTH_URL,
        headers=XingAuthHeaders().model_dump(by_alias=True),
        params=XingAuthParams(appkey=app_key, appsecretkey=app_secret).model_dump()
    )

    if 'error_code' in response.json():
        raise Exception(response.json())

    data = response.json()
    return data["access_token"]
