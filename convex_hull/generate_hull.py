import csv
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
import numpy as np

FILE_LOC = 'test_data.csv'

class Packet:
    def __init__(self, who, when, speed, hdg, lat, lon,
                 del_hdg, avg_del_hdg, dists, deltas, avg_delta, job):
        self.__who = int(who)
        self.__when = when
        self.__speed = int(speed)
        self.__hdg = int(hdg)
        self.__lat = float(lat)
        self.__lon = float(lon)

        self.__del_hdg = float(del_hdg)
        self.__avg_del_hdg = float(avg_del_hdg)
        self.__dists = dists
        self.__deltas = deltas
        self.__avg_delta = float(avg_delta)

        self.__job = bool(int(job))
        self.__cluster_id = -1

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

    def get_avg_del_hdg(self):
        return self.__avg_del_hdg

    def get_dists(self):
        return self.__dists

    def get_deltas(self):
        return self.__deltas

    def get_avg_delta(self):
        return self.__avg_delta

    def get_job(self):
        return self.__job

    def get_cluster_id(self):
        return self.__cluster_id

    def set_cluster_id(self, cluster_id):
        self.__cluster_id = cluster_id


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


def init(data):
    packets = []

    for r in data:
        point = Packet(0, r[0], r[1], r[2], r[4], r[3], r[5], r[15],
                       [ float(r[i]) for i in xrange(6, 11) ],
                       [ float(r[i]) for i in xrange(11, 15) ],
                       r[16], r[17])

        packets.append(point)

    return packets


def collect_pts(packets):
    pts = []

    for point in packets:
        if point.get_job():
            pts.append(list(point.get_loc()))

    return pts


def enum_clusters(packets):
    i = -1
    on_job = False

    for point in packets:
        if not on_job and point.get_job():
            i += 1

        on_job = point.get_job()

        if on_job:
            point.set_cluster_id(i)


def cluster_div(packets):
    divs = {}

    for point in packets:
        cluster_id = point.get_cluster_id()

        if cluster_id == -1:
            continue

        if cluster_id not in divs:
            divs[cluster_id] = []

        divs[cluster_id].append(point)

    matrix = []

    for cluster_id_objs in divs:
        if len(divs[cluster_id_objs]) >= 3: # Needs >=3 for convex hull
            matrix.append(divs[cluster_id_objs])

    return matrix


if __name__ == '__main__':
    data = load_CSV(FILE_LOC)
    del data[0]

    packets = init(data)

    packets.sort(key = lambda point: point.when())
    enum_clusters(packets)

    clustered_packets = cluster_div(packets)

    for cluster in clustered_packets:
        pts = np.array(collect_pts(cluster))
        hull = ConvexHull(pts)

        plt.plot(pts[:, 0], pts[:, 1], 'o')

        for simplex in hull.simplices:
            plt.plot(pts[simplex, 0], pts[simplex, 1], 'k-')

    plt.show()
