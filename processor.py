import csv
from collections import deque
from geopy.distance import vincenty

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


def get_deltas(package):
    last_packet = package[-1] # Last element.
    dists = []

    for i in xrange(WINDOW_SIZE - 2, -1, -1):
        curr_dist = vincenty(last_packet.get_loc(), package[i].get_loc()).miles

        dists.append(curr_dist)

    return [ dists[i + 1] - dists[i] for i in xrange(len(dists) - 1) ]


if __name__ == '__main__':
    packages = create_packages(init(load_CSV(FILE_LOC)))
