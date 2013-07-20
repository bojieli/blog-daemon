
import random
import string


def random_string(N):
    return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(N))

