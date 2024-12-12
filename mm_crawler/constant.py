from enum import Enum
import pytz  # type: ignore

KST = pytz.timezone('Asia/Seoul')

class NaverArticleCategoryEnum(Enum):
    MAIN = "main"

    OUTLOOK = "outlook"
    ANALYSIS = "analysis"
    GLOBAL = "global"
    DERIVATIVES = "derivatives"
    DISCLOSURES = "disclosures"
    FOREX = "forex"

    CODE = "code"