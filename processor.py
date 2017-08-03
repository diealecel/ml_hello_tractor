import csv
from collections import deque
from geopy.distance import vincenty
from numpy import mean

WINDOW_SIZE = 6
DEL_HDG_WINDOW_SIZE = 5
FILE_LOC = 'edit.csv'

class Packet:
    def __init__(self, who, when, speed, hdg, lat, lon):
        self.__who = int(who)
        self.__when = when
        self.__speed = int(speed)
        self.__hdg = int(hdg)
        self.__lat = float(lat)
        self.__lon = float(lon)

        self.__del_hdg = 0
        self.__avg_del_hdg = 0
        self.__dists = []
        self.__deltas = []
        self.__avg_delta = 0

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

    # These are qualities only to be attached in processing

    def get_del_hdg(self):
        return self.__del_hdg

    def set_del_hdg(self, del_hdg):
        self.__del_hdg = del_hdg

    def get_avg_del_hdg(self):
        return self.__avg_del_hdg

    def set_avg_del_hdg(self, avg_del_hdg):
        self.__avg_del_hdg = avg_del_hdg

    def get_dists(self):
        return self.__dists

    def set_dists(self, dists):
        self.__dists = dists

    def get_deltas(self):
        return self.__deltas

    def set_deltas(self, deltas):
        self.__deltas = deltas

    def get_avg_delta(self):
        return self.__avg_delta

    def set_avg_delta(self, avg_delta):
        self.__avg_delta = avg_delta


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
        point = Packet(row[8], row[7], row[4], row[1], row[2], row[3])

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


def get_dists_deltas(package):
    last_packet = package[-1] # Last element.
    dists = []

    for i in xrange(len(package) - 2, -1, -1):
        curr_dist = vincenty(last_packet.get_loc(), package[i].get_loc()).meters

        dists.append(curr_dist)

    return dists, [ dists[i + 1] - dists[i] for i in xrange(len(dists) - 1) ]

def process_packets(packets):
    window = deque()
    del_hdg_window = deque()

    for point in packets:
        # GETTING HDG CHANGE
        last_hdg = window[-1].get_hdg() if len(window) > 0 else 0

        window.append(point)

        # Insert heading change.
        del_hdg = abs(window[-1].get_hdg() - last_hdg)
        del_hdg = 360 - del_hdg if del_hdg > 180 else del_hdg

        window[-1].set_del_hdg(del_hdg)
        del_hdg_window.append(del_hdg)
        # END HDG change

        # -----------------------------

        # GETTING DISTS AND DELTAS AND AVG DELTAS
        dists, deltas = get_dists_deltas(list(window))

        window[-1].set_dists(dists)
        window[-1].set_deltas(deltas)
        window[-1].set_avg_delta(mean(deltas) if len(deltas) > 0 else 0)
        # END DISTS AND DELTAS AND AVG DELTAS

        # -----------------------------

        # GETTING AVG HDG change
        window[-1].set_avg_del_hdg(mean(del_hdg_window))
        # END AVG HDG change

        if len(window) >= WINDOW_SIZE:
            window.popleft()

        if len(del_hdg_window) >= DEL_HDG_WINDOW_SIZE:
            del_hdg_window.popleft()


if __name__ == '__main__':
    # packages = create_packages(init(load_CSV(FILE_LOC)))
    packets = init(load_CSV(FILE_LOC))
    process_packets(packets)

    matrix = []

    for packet in packets:
        row = []

        row.append(packet.when())
        row.append(packet.get_speed())
        row.append(packet.get_hdg())
        row.append(packet.get_loc()[0])
        row.append(packet.get_loc()[1])
        row.append(packet.get_del_hdg())

        i = 0
        for dist in packet.get_dists():
            row.append(dist)
            i += 1
        for j in xrange(5 - i):
            row.append(0)

        i = 0
        for delta in packet.get_deltas():
            row.append(delta)
            i += 1
        for j in xrange(4 - i):
            row.append(0)

        row.append(packet.get_avg_del_hdg())
        row.append(packet.get_avg_delta())

        matrix.append(row)

    with open('test.csv', 'w') as test:
        writer = csv.writer(test)

        writer.writerows(matrix)
