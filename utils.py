import cv2
import matplotlib.pyplot as plt
import numpy as np
from queue import Queue
import time
import random
import math
import argparse
from datetime import datetime
import logging
import png
import os
import itertools

# calculate the luminance given a bounding box for an image `img`
# serves as a helper function for `find_largest_bounding_box()`
def calc_lum(img, box):
    return np.mean(img[box[0]:box[2], box[1]:box[3]])

# given a binary image where the "on" pixels are part of the gel
# and the "off" pixels are not part of the gel, find the largest
# bounding box for the gel
def find_largest_bounding_box(img, delta=10):
    box = [0, 0, img.shape[0], img.shape[1]] #x1, y1, x2, y2
    while True:
        mod = box
        orig_box = box
        if calc_lum(img, [box[0] + delta, box[1], box[2], box[3]]) > calc_lum(img, box):
            box = [box[0] + delta, box[1], box[2], box[3]]
            mod = box
        if calc_lum(img, [box[0], box[1] + delta, box[2], box[3]]) > calc_lum(img, box):
            box = [box[0], box[1] + delta, box[2], box[3]]
            mod = box
        if calc_lum(img, [box[0], box[1], box[2] - delta, box[3]]) > calc_lum(img, box):
            box = [box[0], box[1], box[2] - delta, box[3]]
            mod = box
        if calc_lum(img, [box[0], box[1], box[2], box[3] - delta]) > calc_lum(img, box):
            box = [box[0], box[1], box[2], box[3] - delta]
            mod = box
        if box == orig_box:
            break
    return box

def inbounds(img, i, j):
    return (0 <= i < img.shape[0]) and (0 <= j < img.shape[1])

# help find the set of highlighted pixels connected
# to the given (i,j) pixel
def find_one_blob_helper(thresholded, i, j):
    q = Queue()

    visited = set()
    visited.add((i, j))

    contour = set()

    q.put((i + 1, j))
    q.put((i - 1, j))
    q.put((i, j + 1))
    q.put((i, j - 1))

    while q.qsize() != 0:
        pos = q.get()
        if pos in visited:
            continue

        if inbounds(thresholded, pos[0], pos[1]) and thresholded[pos[0], pos[1]] > 0:
            visited.add(pos)

            q.put((pos[0] + 1, pos[1]))
            q.put((pos[0] - 1, pos[1]))
            q.put((pos[0], pos[1] + 1))
            q.put((pos[0], pos[1] - 1))
        else:
            contour.add(pos)

    return visited, contour

# find sets of pixels for blobs in an image of gel
def find_blobs(thresholded, min_area=1, max_area=9999999, min_circularity=0, threshold_val=100):
    # stores all pixels that pass the threshold
    # we want this so that we have quick access
    # to the next blob pixel (and not have to search through)
    blob_pixel_set = set(tuple(x) for x in np.array(np.where(thresholded > threshold_val)).T)

    blobs = []
    contours = []
    blob_num = 1
    filtered_mina = 0
    filtered_maxa = 0
    filtered_minc = 0

    overall_start = time.time()

    while len(blob_pixel_set) != 0:
        logging.debug('finding blob #{}...'.format(blob_num))

        start = time.time()
        # get a random blob pixel we haven't bfs'ed through yet and
        # bfs through it, returning the blob's blob set and contour set
        start_pixel = random.sample(blob_pixel_set, 1)[0]
        blob, contour = find_one_blob_helper(thresholded, *start_pixel)

        logging.debug('started at ({}, {})'.format(*start_pixel))
        logging.debug('took {:.3g} seconds'.format(time.time() - start))

        blob_pixel_set = blob_pixel_set.difference(blob)  # subtract the blob from the set

        circularity = 4*math.pi*len(blob) / (len(contour))**2

        if len(blob) == 0:
            break
        elif len(blob) < min_area:
            logging.debug('blob area was only {} < min_area ({}) ... discarded'.format(len(blob), min_area))
            filtered_mina += 1
            continue
        elif len(blob) > max_area:
            logging.debug('blob area was {} > max_area ({}) ... discarded'.format(len(blob), max_area))
            filtered_maxa += 1
            continue
        elif circularity < min_circularity:
            logging.debug(("circularity was {:.3g} / {:.3g} = {:.3g} <"
                   " min_circularity ({:.3g}) ... discarded").format(4*math.pi*len(blob),
                                                                 (len(contour))**2,
                                                                 circularity,
                                                                 min_circularity))
            filtered_minc += 1
            continue

        blobs.append(blob)
        contours.append(contour)
        blob_num += 1
        logging.debug('blob area was {}'.format(len(blob)))
        logging.debug('blob contour length was {}'.format(len(contour)))
        logging.debug('blob circularity was {:.3g}'.format(circularity))

    logging.debug('found {} blobs (filtered {} out) in {:.3g} seconds'.format(blob_num,
                                                                      filtered_mina + filtered_maxa + filtered_minc,
                                                                      time.time() - overall_start))
    return blobs, contours, [filtered_mina, filtered_maxa, filtered_minc]

def pixset2xy(pixset):
    x, y = np.array(list(zip(*[(y, x) for x,y in pixset])))
    return (x, y)

# find the "center of mass" of a given blob
# while randomly sampling only `sampling` fraction of
# the entire blob (to speed up compute)
def get_blob_com(blob, sampling=0.1):
    return tuple(sum(X[i] for X in itertools.islice(blob, int(len(blob) * sampling))) / (len(blob) * sampling) for i in range(1, -1, -1))

# calculate the luminance of a given blob
# method: '{meaned, demeaned}-{avg, total}'
def get_blob_lum(lum_img, blob, method='meaned-avg', avg_noise=0):
    blob_lum = np.sum([lum_img[X] for X in blob])
    if method.split('-')[0] == 'demeaned':
        blob_lum -= avg_noise * len(blob)
    if method.split('-')[1] == 'avg':
        blob_lum /= len(blob)
    return blob_lum

# calculate the average noise of the gel
# (outside of the blobs)
def get_avg_noise(red, blue):
    return np.mean(red[blue > 100])

# generate a set containing (COM, LUM)
# ultimate purpose of this is to plot
# these onto the original image
def gen_blob_lum_info(blobs, lum_img, blue_img=None, get_total=False):
    info = set()
    method = ['meaned', 'avg']
    if not blue_img is None:
        avg_noise = get_avg_noise(lum_img, blue_img)
        method[0] = 'demeaned'
    else:
        avg_noise = 0
    if get_total:
        method[1] = 'total'

    method = '-'.join(method)
    baseline_exp = None

    for i, blob in enumerate(blobs):
        logging.debug('getting "center of mass" of blob #{}'.format(i + 1))
        com = get_blob_com(blob)
        logging.debug('getting luminance of blob #{}'.format(i + 1))
        lum = get_blob_lum(lum_img, blob, method=method, avg_noise=avg_noise)
        if baseline_exp is None:
            baseline_exp = math.ceil(math.log10(lum))
        lum /= 10**(baseline_exp - 1)
        info.add((com, lum))
    return info

