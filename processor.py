import csv
from collections import deque

WINDOW_SIZE = 6
FILE_LOC = ''

class Packet:
    def __init__(self, who, when, speed, hdg, lat, lon):
        self.__who = who
        self.__when = when
        self.__speed = speed
        self.__hdg = hdg
        self.__lat = lat
        self.__lon = lon

    def who(self):
        return self.__who

    def when(self):
        return self.__when

    def get_speed(self):
        return self.__speed

    def get_hdg(self):
        return self.__hdg

    def get_loc(self):
        return self.__lat, self.__lon


def load_CSV(filename):
    matrix = []

    with open(filename) as f:
        reader = csv.reader(f)

        for row in reader:
            string_row = []

            for value in row:
                string_row.append(value)

            matrix.append(string_row)

    return matrix


# Converts all data points into Packet objects.
def init(data):
    packets = []

    for row in data:
        point = Packet(row[0], row[7], row[4], row[1], row[2], row[3])

        packets.append(point)

    return packets


# Segments packets into packages of |WINDOW_SIZE|.
def create_packages(packets):
    packages = []
    window = deque()

    # Initial window.
    for i in xrange(WINDOW_SIZE):
        window.append(packets[i])

    packages.append(list(window))

    # Remaining windows.
    for i in xrange(WINDOW_SIZE, len(packets)):
        window.popleft()
        window.append(packets[i])

        packages.append(list(window))

    return packages


if __name__ == '__main__':
    packets = init(load_CSV(FILE_LOC))
