<img src="https://imgur.com/ClAtuZ9.png" width="300">

# gscan

> Analyze your electrophoresis gels in seconds.

Scan an image of an electrophoresis gel and obtain luminance data of the bands in seconds. Use this if you don't have a Q-PCR machine.

## Example

The following example scans the `gelsample1.jpg` image using a threshold of 150 (only considers pixels whose red channel is greater than 150), minimum area of 40 pixels (only considers band candidates that have at least 40 pixels within them), and minimum "circularity" of at least 0.1 (only considers band candidates that are at least 0.1 "circular" as defined here in this [Wikipedia article](https://en.wikipedia.org/wiki/Shape_factor_(image_analysis_and_microscopy)#Circularity)):
```shell
python scanner.py --input gelsample1.jpg --threshold 100 --minA  --minC 0.1
```

The following images were produced with a simpler command:
```shell
python scanner.py --input gelsample1.jpg
```

<div class="imgc">
    <p>
    <img src="https://imgur.com/5kkxs2T.png" width=400px style="float:left;">
    <img src="https://imgur.com/pDoXRYj.png" width=400px style="float:right;">
</div>

---

## Installation

No installation necessary other than dependencies, which are:
- OpenCV
- NumPy
- Matplotlib
- PyPNG

### Using a virtual environment

Create your virtual environment:
```shell
virtualenv env
```
Activate it:
```shell
source env/bin/activate
```
Install packages via `pip`:
```shell
pip install opencv-python numpy matplotlib pypng
```

Clone this repository
```shell
git clone https://github.com/rodrigo-castellon/gscan.git && cd gscan
```

Now you can use `scanner.py` on any image! If you have an image `gelsample1.jpg` you would like to analyze, put it in the repository root directory `gscan` and just type
```shell
python scanner.py --input gelsample1.jpg
```

## Troubleshooting and Tips

Running the script won't always work right out of the box, and it'll take a bit of fiddling for it to work well with your use case. Here are some step-by-step tips that will speed up getting to the scan you want:

1. The very first thing you should do is run `$ python scanner.py --input INPUT_IMAGE.jpg` and check what `images/INPUT_IMAGE/blob_binary.png` looks like. If it's all white, run with a higher threshold like so `$ python scanner.py --input INPUT_IMAGE.jpg --threshold 150` (150 is just an example; the default threshold is 100). If it's all black, run with a lower threshold like so `$ python scanner.py --input INPUT_IMAGE.jpg --threshold 75` (75 is just an example as well). Keep doing this until the bands are well-defined in the `blob_binary.png` image. An simple automatic thresholding algorithm is in the works so you won't have to do this in the future.

2. Once you can see the bands clearly in the `blob_binary.png` image (let's say with threshold `140`), you should run with no filters with `$ python scanner.py --input INPUT_IMAGE.jpg --threshold 140 -n` and check what the output scanned image looks like (this image is named `out--YEAR-MONTH-DAY HOUR-MINUTE-SECOND.png`). If it contains all of the correctly labeled luminances you need, you're almost there! If not, I'm sorry and let me know so I can try taking into account this edge case (building up a repository of test cases is also in the works so this doesn't happen).

3. Adjust `--minA` (minimum area of a "blob", which is a contiguous blob of pixels in `blob_binary.png`) and `--maxA` (maximum area of a "blob") and `--minC` (minimum circularity of a "blob", which ranges from 0 to 1) to filter out noise and scan only the bands. For example, you could run the command `$ python scanner.py -i INPUT_IMAGE.jpg --threshold 140 --minA 50 --maxA 9000 --minC 0.2`.

4. (Optional) Use `-m` (mean) to prevent demeaning of blob luminances or `-a` to get the average luminance of bands rather than total luminance.

## To-Do

- Make algorithm more efficient
    - takes several seconds per image scan right now... not as good as it could be √ (now takes 1-5 seconds rather than 20+ seconds)
    - could make it even faster
- Make a GUI or make the interface easier to use somehow (figure this out later)
- Add automatic thresholding
    - create a regressor (or use some heuristics/rules) to determine how good a threshold value is for an image
        - needs to be more complex than just "proportion of image that is activated after threshold"
        - Could use Naive Bayes trained on a bunch of features I come up with, or maybe an SVM, but I'd need more data for that (maybe Google images!)
        - cool idea: https://arxiv.org/pdf/1808.00257.pdf (probably won't be useful though)
    - optimize the regressor over threshold values in 0..255
- Cache (image, threshold) -> (blob set) so that the same blobs don't have to be calculated over and over again
- Refactor `utils.py`
    - Add `Blob` class
    - Conform function docstrings to PEP

