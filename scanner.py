'''
Author: Rodrigo Castellon
Program Description:
Scan a given image of an electrophoresis gel for bands,
then find the luminances of the bands and output a modified
image containing the bands labeled with their luminance levels
as another image file.
'''

from utils import *

parser = argparse.ArgumentParser(description = ('Scan a given electrophoresis gel image for band luminances '
                                                'and write the image labeled with luminances to an output image. Tips: '
                                                '(1) It is always better to crop your input image such that it includes '
                                                'only the bands and the lane markings (so you can tell which bands '
                                                'are which). (2) Make sure to fiddle with --threshold so that the image '
                                                '`images/YOURIMAGENAMEHERE/blob_binary.png` looks like it separates '
                                                'out the bands properly BEFORE you start fiddling with other filtering '
                                                'arguments.'))
requiredNamed = parser.add_argument_group('required named arguments')
requiredNamed.add_argument('-i', '--input', help='choose the input image file to scan', type=str, required=True, default='TEL1.jpg')
parser.add_argument('--threshold', help='choose the threshold value used to filter for bands (default: 100; increase this parameter if blob_binary.png is all white, and decrease if blob_binary.png is all black)', type=int, default=100)
parser.add_argument('--minA', help='choose the minimum area of a blob to be considered as a band (default: 0.4 * (img.shape[0] + img.shape[1]) / 2)', type=int, default=-1)
parser.add_argument('--maxA', help='choose the maximum area of a blob to be considered as a band (default: 10 * (img.shape[0] + img.shape[1]) / 2)', type=int, default=-1)
parser.add_argument('--minC', help='choose the minimum "circularity" of a blob to be considered a band (default: 0.4)', type=float, default=0.4)
parser.add_argument('-o', '--out', help='choose the output image file to write to', type=str, default='out--{}.png'.format(datetime.now().strftime('%Y-%m-%d %I-%M-%S')))
parser.add_argument('-m', '--mean', help='don\'t de-mean the luminance values by subtracting background noise (i.e. average luminance of surrounding gel)', action='store_true')
parser.add_argument('-a', '--avg', help='get the average luminance of the bands rather than the total luminance', action='store_true')
parser.add_argument('-k', '--keep', help='keep the image\'s original resolution; don\'t downscale to perform computations', action='store_true')
parser.add_argument('-n', '--none', help='no filters at all', action='store_true')
parser.add_argument('--height', help='choose the height of the downscaled image (we downscale to speed up computation)', type=int, default=800)
args = parser.parse_args()

input_file = args.input
output_file = args.out
min_area = args.minA
max_area = args.maxA
min_circ = args.minC
BLOB_THRESHOLD_VAL = args.threshold
mean = args.mean
avg = args.avg
keep = args.keep
none = args.none
if none:
    min_area = 0
    max_area = 9999999
    min_circ = 0
NEW_HEIGHT = args.height
GEL_THRESHOLD_VAL = 100

folders_to_create = ['images', 'logs']
for folder_to_create in folders_to_create:
    if not os.path.exists(os.path.join(folder_to_create, '{}'.format(os.path.splitext(input_file)[0]))):
        os.makedirs(os.path.join(folder_to_create, '{}'.format(os.path.splitext(input_file)[0])))

# set up logging to file
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %I:%M:%S',
                    filename=os.path.join('logs', '{}'.format(os.path.splitext(input_file)[0]), 'scan--{}.log'.format(datetime.now().strftime('%Y-%m-%d %I-%M-%S'))),
                    filemode='w')

# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)
# Now, we can log to the root logger, or any other logger. First the root...
logging.info('scanning {}...'.format(input_file))

start = time.time()
img = cv2.imread(input_file)

aspect_ratio = img.shape[1] / img.shape[0]

if not keep:
    img = cv2.resize(img, (int(NEW_HEIGHT * aspect_ratio), NEW_HEIGHT), interpolation=cv2.INTER_AREA)

# "resolutionality" is just a quantity we use to quantify how much resolution the image has
# we use this quantity to determine default filter quantities (min_area and max_area)
resolutionality = (img.shape[0] + img.shape[1]) / 2

# follow through with the actual defaults
if min_area == -1:
    min_area = 0.4 * resolutionality
if max_area == -1:
    max_area = 10 * resolutionality

logging.info('parameters: min_area={}; max_area={}; min_circularity={}; BLOB_THRESHOLD_VAL={}; mean={}; avg={}'.format(min_area, max_area, min_circ, BLOB_THRESHOLD_VAL, mean, avg))

red = img[..., 2]
blue = img[..., 0]

png.from_array(red.astype('uint8'), 'L').save(os.path.join('images', '{}'.format(os.path.splitext(input_file)[0]), 'red.png'))
png.from_array(blue.astype('uint8'), 'L').save(os.path.join('images', '{}'.format(os.path.splitext(input_file)[0]), 'blue.png'))

# `gel_binary` is an array that encodes 255 if it
# is part of the gel and 0 if it is not part of the gel.
# this will help us determine the largest bounding box
# for the gel
gel_binary = np.zeros((blue.shape), dtype='uint8')
gel_binary[np.where(blue > GEL_THRESHOLD_VAL)] = 255

png.from_array(gel_binary, 'L').save(os.path.join('images', '{}'.format(os.path.splitext(input_file)[0]), 'gel_binary.png'))

logging.info('finding largest bounding box...')
bounding_box_start = time.time()
gel_bounds = find_largest_bounding_box(gel_binary)

logging.debug('found largest bounding box, {}, in {:.3g} seconds'.format(gel_bounds, time.time() - start))

# this shows the image once we have cropped out everything
# but the gel
newred = red[gel_bounds[0]:gel_bounds[2], gel_bounds[1]:gel_bounds[3]].astype('uint8')
png.from_array(newred, 'L').save(os.path.join('images', '{}'.format(os.path.splitext(input_file)[0]), 'newred.png'))

# we will use the red channel from this point on because it
# its peaks correspond to the bands


# `band_binary` is an array that stores 255 if
# a pixel has value greater than 100 in the newred
# array, and 0 if not. It helps to store a binary
# image encoding of the bands (as can be seen in
# the plot)
blob_binary = np.zeros((newred.shape), dtype='uint8')
blob_binary[np.where(newred > BLOB_THRESHOLD_VAL)] = 255
png.from_array(blob_binary, 'L').save(os.path.join('images', '{}'.format(os.path.splitext(input_file)[0]), 'blob_binary.png'))

logging.info('finding blobs in the image...')
blob_start = time.time()
blobs, contours, filtered_nums = find_blobs(blob_binary, min_area=min_area, max_area=max_area, min_circularity=min_circ)

logging.info('completed in {:.3g} seconds'.format(time.time() - blob_start))

blob_filter_str_report = 'found {} blobs ('.format(len(blobs))
for filtered_num, phrase in zip(filtered_nums, ['area too small', 'area too large', 'not circular enough']):
    if filtered_num != 0:
        blob_filter_str_report += 'filtered {} because {}, '.format(filtered_num, phrase)

if len(blobs) == 0:
    logging.error(blob_filter_str_report + 'please view the ' + os.path.join('images', '{}'.format(os.path.splitext(input_file)[0])) + ' folder as well as the ' + os.path.join('logs', '{}'.format(os.path.splitext(input_file)[0])) + ' folder for more information.)')
else:
    blob_filter_str_report = blob_filter_str_report[:-2]
    if sum(filtered_nums) != 0:
        blob_filter_str_report += ')'
    logging.info(blob_filter_str_report)

logging.info('finding the luminances...')
lum_start = time.time()
if not mean:
    newblue = blue[gel_bounds[0]:gel_bounds[2], gel_bounds[1]:gel_bounds[3]].astype('uint8')
else:
    newblue = None
info = gen_blob_lum_info(blobs, newred, newblue, get_total=not(avg))

logging.info('found luminances in {:.3g} seconds'.format(time.time() - lum_start))

to_show = img[gel_bounds[0]:gel_bounds[2], gel_bounds[1]:gel_bounds[3],::-1]

plt.ioff()  # turn interactive mode off
plt.imshow(to_show)
for x, y in (pixset2xy(contour) for contour in contours):
    plt.scatter(x, y, color='red', s=0.01)

for ((x,y), lum) in info:
    plt.text(x - 0*0.02*resolutionality, y - 0*0.02*resolutionality, '{:.3}'.format(lum), color='red', fontsize=4, ha='center', va='center')

plt.title('Gel band luminance from {}\nparameters: min_area={}\n max_area={}\n min_circularity={}\n BLOB_THRESHOLD_VAL={}\n mean={}\n avg={}'.format(input_file, min_area, max_area, min_circ, BLOB_THRESHOLD_VAL, mean, avg))

plt.savefig(output_file, bbox_inches='tight', dpi=500)
logging.info('saved output image to "{}"'.format(output_file))
logging.info('finished program after {:.3g} seconds'.format(time.time() - start))
