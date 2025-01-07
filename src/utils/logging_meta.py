from loguru import logger


class LoggingMeta(type):

    def __new__(mcs, name, bases, local):
        for attr in local:
            value = local[attr]
            if value.__class__ is type:
                continue
            if callable(value):
                local[attr] = logger.catch(value)
        return type.__new__(mcs, name, bases, local)
