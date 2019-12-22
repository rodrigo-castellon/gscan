# gscan

> Analyze your electrophoresis gels in seconds.

Scan an image of an electrophoresis gel and obtain luminance data of the bands in seconds. Use this if you don't have a Q-PCR machine.

## Example

The following example scans the `gelsample1.jpg` image using a threshold of 150 (only considers pixels whose red channel is greater than 150), minimum area of 40 pixels (only considers band candidates that have at least 40 pixels within them), and minimum "circularity" of at least 0.1 (only considers band candidates that are at least 0.1 "circular" as defined here in this [Wikipedia article](https://en.wikipedia.org/wiki/Shape_factor_(image_analysis_and_microscopy)#Circularity)):
```shell
python scanner.py --input gelsample1.jpg --threshold 150 --minA 40 --minC 0
```

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
Now you can use `scanner.py` on any image! If you have an image `gelsample1.jpg` you would like to analyze, just type
```shell
python scanner.py --input gelsample1.jpg
```
