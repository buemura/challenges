import itertools
from functools import reduce


class LazyCollection:
    def __init__(self, iterable):
        self.iterable = iterable

    def map(self, func):
        return LazyCollection(map(func, self.iterable))

    def filter(self, predicate):
        return LazyCollection(filter(predicate, self.iterable))

    def reduce(self, func, initializer=None):
        if initializer is not None:
            return reduce(func, self.iterable, initializer)
        return reduce(func, self.iterable)

    def chunk(self, size):
        def generator():
            it = iter(self.iterable)
            while chunk := list(itertools.islice(it, size)):
                yield chunk

        return LazyCollection(generator())

    def paginate(self, page_number, page_size):
        start = page_number * page_size
        return itertools.islice(self.iterable, start, start + page_size)

    def __iter__(self):
        return iter(self.iterable)


data = range(1, 11)  # 1 through 10

result = (
    LazyCollection(data)
    .map(lambda x: x * 2)  # Multiply by 2
    .filter(lambda x: x % 2 == 0)  # Filter the even numbers
    .chunk(3)  # Break into chunks of 3
)

for chunk in result:
    print(chunk)
