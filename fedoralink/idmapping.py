

def url2id(url):
    """
        Serialize url into a number that is compatible with django ids
    """
    return int.from_bytes(url.encode('utf-8'), byteorder='big', signed=False)


def id2url(django_id):
    """
        Return url out of django id created by url2id
    """
    num_bytes = django_id.bit_length() // 8 + 1
    return django_id.to_bytes(num_bytes, byteorder='big', signed=False).decode('utf-8')
