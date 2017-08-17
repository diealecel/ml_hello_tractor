# -*- coding: utf-8 -*-

import csv, sys
from pyproj import Proj
from numpy import linspace

FILE_LOC = 'test_data.csv'
PROJECTION = 'utm'

# Using Hausdorff method
GRANULARITY = 500


def print_progress(iteration, total, prefix = '', suffix = '', decimals = 2, bar_length = 100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    # Print new line when complete
    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()


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

        self.__xy = None

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

    def get_xy(self):
        return self.__xy

    def set_xy(self, xy):
        self.__xy = xy


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


def find_xy(clusters):
    converter = Proj(proj = PROJECTION)

    for cluster in clusters:
        for pt in cluster:
            lat, lon = pt.get_loc()
            pt.set_xy(converter(lat, lon))


def get_min_max(cluster):
    x_i, y_i = cluster[0].get_xy()
    x_min = x_max = x_i
    y_min = y_max = y_i

    for i in xrange(1, len(cluster)):
        x, y = cluster[i].get_xy()

        if x < x_min:
            x_min = x
        if x > x_max:
            x_max = x
        if y < y_min:
            y_min = y
        if y > y_max:
            y_max = y

    return x_min, x_max, y_min, y_max


class Cell:
    def __init__(self, x_min, x_max, y_min, y_max):
        self.__xrng = x_min, x_max
        self.__yrng = y_min, y_max
        self.__used = False

    def get_xrng(self):
        return self.__xrng

    def get_yrng(self):
        return self.__yrng

    def used(self):
        return self.__used

    def set_used(self, used):
        self.__used = used


class Grid:
    def __init__(self, x_min, x_max, y_min, y_max):
        self.__used_cells = None

        rows = list(linspace(y_min, y_max, GRANULARITY))
        cols = list(linspace(x_min, x_max, GRANULARITY))

        self.__total_cells = (len(rows) - 1) * (len(cols) - 1)

        self.__grid = [] # Row-major.

        for i in xrange(len(rows) - 1):
            y_min = rows[i]
            y_max = rows[i + 1]

            grid_cells = []

            for j in xrange(len(cols) - 1):
                x_min = cols[j]
                x_max = cols[j + 1]

                curr = Cell(x_min, x_max, y_min, y_max)
                grid_cells.append(curr)

                print_progress(i * (len(rows) - 1) + j + 1,
                               self.__total_cells,
                               'Creating grid...  ')

            self.__grid.append(grid_cells)

    # To be optimized later to use binary search trees, but O(n^2) for now.
    def load_grid(self, cluster):
        for pt in xrange(len(cluster)):
            x, y = cluster[pt].get_xy()

            r_index = None
            for i in xrange(len(self.__grid)):
                y_min, y_max = self.__grid[i][0].get_yrng()

                if y >= y_min and y <= y_max:
                    r_index = i
                    break

            c_index = None
            for i in xrange(len(self.__grid[0])):
                x_min, x_max = self.__grid[0][i].get_xrng()

                if x >= x_min and x <= x_max:
                    c_index = i
                    break

            self.__grid[r_index][c_index].set_used(True)

            print_progress(pt + 1,
                           len(cluster),
                           'Loading grid...   ')

    def complete_grid(self):
        self.__used_cells = 0

        for r in xrange(len(self.__grid)):
            min_index = max_index = None

            for c in xrange(len(self.__grid[r])):
                if self.__grid[r][c].used():
                    if not min_index:
                        min_index = c
                    elif not max_index:
                        max_index = c
                    else:
                        max_index = c if c > max_index else max_index

                print_progress(r * len(self.__grid[r]) + c + 1,
                               self.__total_cells,
                               'Completing grid...')

            if not min_index or not max_index:
                continue

            for c in xrange(len(self.__grid[r])):
                if c >= min_index and c <= max_index:
                    self.__used_cells += 1

        print float(self.__used_cells) / self.__total_cells





def find_area(cluster):
    x_min, x_max, y_min, y_max = get_min_max(cluster)

    grid = Grid(x_min, x_max, y_min, y_max)
    grid.load_grid(cluster)
    grid.complete_grid()



if __name__ == '__main__':
    data = load_CSV(FILE_LOC)
    del data[0]

    packets = init(data)
    packets.sort(key = lambda pt: pt.when())

    enum_clusters(packets)
    clusters = cluster_div(packets)

    find_xy(clusters)

    for cluster in clusters:
        find_area(cluster)
