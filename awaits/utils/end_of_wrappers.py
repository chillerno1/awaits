from awaits.errors import IncorrectUseOfTheDecoratorError


def end_of_wrappers(args, wrapper):
    """
    We define whether the decorator is called as a decorator factory (that is, with no positional arguments) or as an immediate decorator.
    """
    if not len(args):
        return wrapper
    elif len(args) == 1 and callable(args[0]):
        return wrapper(args[0])
    raise IncorrectUseOfTheDecoratorError('You used the awaitable decorator incorrectly. Read the documentation.')
