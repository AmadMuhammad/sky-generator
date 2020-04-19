# Libraries
import math
from multiprocessing import Process, Array
import numpy as np
from PIL import Image
import functions as fun
import variables as var


# Geometry
height = 1                                                  # position of camera from sea level (m) (max: 60km)
cam_pos = np.array([0, 0, var.Re+height], dtype=np.int64)   # position of camera
earth_center = np.array([0, 0, 0])                          # center of Earth
# Sun rotation
sun_lat = math.radians(60)
sun_lon = math.radians(0)
# normalize sun rotation
sun_rot = fun.normalize(sun_lat, 0)
# divisions of the rays (more divisions make more accurate results)
samples = 20
# number of processes (squared number must be near the number of logic processors of the CPU)
nproc = 3
# image size (in pixels)
pixelsx = 128
pixelsy = 64

# image definition
img = Image.new('RGB', (pixelsx, pixelsy), "black")
pixels = img.load()
img_shifted = Image.new('RGB', (pixelsx, pixelsy), "black")
pixels_shifted = img_shifted.load()


def calc_pixel(xmin, xmax, ymin, ymax, pix):
    for i in range(xmin, xmax):
        for j in range(ymin, ymax):
            # camera rotation
            cam_lat = math.radians((1-j/pixelsy)*90)
            cam_lon = math.radians(i/pixelsx*360-180)
            # normalize camera rotation
            cam_rot = fun.normalize(cam_lat, cam_lon)
            # get pixel rgb
            rgb = fun.get_rgb(sun_rot, cam_pos, cam_rot, earth_center, samples)
            # print to pixels array in shared memory
            for l in range(3):
                pix[i*3*pixelsy+j*3+l] = int(rgb[l])


def multiprocess():
    processes = []
    halfx = int(pixelsx/2)
    # create shared memory array (that can be accessed by multiple processes at the same time)
    pix = Array('i', halfx*pixelsy*3)
    # split the image in nproc**2 processes
    for i in range(nproc):
        for j in range(nproc):
            p = Process(target=calc_pixel, args=(
                int((halfx/nproc)*j), int((halfx/nproc)*(j+1)), int((pixelsy/nproc)*i), int((pixelsy/nproc)*(i+1)), pix,
            ))
            processes.append(p)
            p.start()
    # wait until all processes end
    for p in processes:
        p.join()
    # print to final pixels
    for i in range(halfx):
        for j in range(pixelsy):
            pixels[i, j] = (pix[i*3*pixelsy+j*3], pix[i*3*pixelsy+j*3+1], pix[i*3*pixelsy+j*3+2])
            pixels[pixelsx-i-1, j] = (pix[i*3*pixelsy+j*3], pix[i*3*pixelsy+j*3+1], pix[i*3*pixelsy+j*3+2])
    # shift pixels with sun lon change
    shift = int(sun_lon/(math.pi*2)*pixelsx)
    s = 0
    for x in range(pixelsx):
        for y in range(pixelsy):
            if x+shift<pixelsx:
                pixels_shifted[x+shift, y] = pixels[x, y]
            else:
                if s<shift:
                    pixels_shifted[s, y] = pixels[x, y]
                    if y==pixelsy-1:
                        s += 1

    # open image
    img_shifted.show()


# multiprocessing
if __name__ == '__main__':
    multiprocess()