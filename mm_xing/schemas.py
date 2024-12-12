from typing import Callable

from pydantic import BaseModel


class XingAuthHeaders(BaseModel):
    content_type: str = "application/x-www-form-urlencoded"

    class Config:
        alias_generator = lambda x: "content-type" if x == "content_type" else x # noqa

class XingAuthParams(BaseModel):
    grant_type: str = "client_credentials"
    appkey: str | None
    appsecretkey: str | None
    scope: str = "oob"

class XingTrHeaders(BaseModel):
    content_type: str = "application/json; charset=utf-8"
    authorization: str
    tr_code: str = ""
    tr_cont: str = "N"
    tr_cont_key: str = ""
    mac_address: str = ""

    class Config:
        alias_generator = lambda x: "tr_cd" if x == "tr_code" else x # noqa

    def update_tr_code(self, tr_code: str):
        self.tr_code = tr_code

    @classmethod
    def update_access_token(cls, access_token: str):
        return cls(
            authorization=f"Bearer {access_token}"
        )

class XingDataConfig(BaseModel):
    path: str
    tr_code: str
    inblock: BaseModel
    cb_handler: Callable = lambda x: x 