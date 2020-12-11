
from ... import TransactionError


DEFAULT_ERROR_MESSAGE = (
    "Unable to process the transaction. " "Transaction's token is incorrect or expired."
)


class AuthorizeNetException(Exception):
    pass
