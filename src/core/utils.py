import unicodedata


def unaccent(text):
    return str(unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8'))
