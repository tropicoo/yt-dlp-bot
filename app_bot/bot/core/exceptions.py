class ConfigError(Exception):
    pass


class InvalidBodyError(Exception):
    pass


class UserAlreadyExistsError(ConfigError):
    """Raised by the config manager so the caller can word its own message.

    A user-facing message cannot be built down here: it has to be written in
    whichever language the admin who asked reads.
    """


class UserNotFoundError(ConfigError):
    pass


class CannotDeleteAdminError(ConfigError):
    pass
