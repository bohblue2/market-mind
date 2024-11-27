from enum import Enum


class RunNames(Enum):
    CONDENSE_QUESTION = "CondenseQuestion"
    HAS_CHAT_HISTORY_CHECK = "HasChatHistoryCheck"
    RETRIEVAL_CHAIN_WITH_HISTORY = "RetrievalChainWithHistory"
    ITEMGETTER_QUESTION = "Itemgetter:question"
    RETRIEVAL_CHAIN_WITH_NO_HISTORY = "RetrievalChainWithNoHistory"
    ROUTE_DEPENDING_ON_CHAT_HISTORY = "RouteDependingOnChatHistory"