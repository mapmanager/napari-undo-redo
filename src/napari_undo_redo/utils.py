def setsAreEqual(a, b):
    """Convenience function. Return true if sets (a, b) are equal."""
    if a is None or b is None:
        return False

    if len(a) != len(b):
        return False

    for x in a:
        if x not in b:
            return False

    return True
