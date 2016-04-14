import numpy as np
import cv2

grayimages = []
images = [
    './pink1.jpg',
    './pink2.jpg',
    './pink3.jpg',
    './pink4.jpg'
    ]

overlay = './reflect.png'

overlay2 = './Text.png'

grids = [
    [(0, 0), (1447, 553)],
    [(1464, 0), (1920, 553)],
    [(0, 570), (739, 1080)],
    [(756, 570), (1920, 816)]
    ]

positions = [0, 0, 0, 0]
positions2 = [0, 0, 0, 0]

directions = [
    (0, -1), # bottom -> top
    (1, 0), # left -> right
    (0, -1),
    (0, 1)  # top -> bottom
    ]
    
framecnt = 0
fps = 60
resolution = (1920, 1080)

output = cv2.VideoWriter('./sample.avi',
                         cv2.cv.CV_FOURCC('X', 'V', 'I', 'D'),
                         fps,
                         resolution)

for i in xrange(len(images)):
    images[i] = cv2.imread(images[i])
    height, width = images[i].shape[:2]
    if (grids[i][1][0] - grids[i][0][0]) / float(width) * height < grids[i][1][1] - grids[i][0][1]:
        images[i] = cv2.resize(images[i], None,
                               fx = (grids[i][1][1] - grids[i][0][1]) / float(height),
                               fy = (grids[i][1][1] - grids[i][0][1]) / float(height),
                               interpolation = cv2.INTER_CUBIC)
    else:
        images[i] = cv2.resize(images[i], None,
                               fx = (grids[i][1][0] - grids[i][0][0]) / float(width),
                               fy = (grids[i][1][0] - grids[i][0][0]) / float(width),
                               interpolation = cv2.INTER_CUBIC)
    grayimages.append(cv2.cvtColor(cv2.cvtColor(images[i], cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR))

overlay = cv2.imread(overlay, -1)
overlay2 = cv2.imread(overlay2, -1)

positions[0] = (0, 553)
positions[1] = (1464 - images[1].shape[1], 0)
positions[2] = (0, 1080)
positions[3] = (756, 570 - images[3].shape[0])

position_overlay = (1920, 760)
direction_overlay = (-1, 0)

def insideGrid(point, grid):
    return grid[0][0] <= point[0] and point[0] <= grid[1][0] and grid[0][1] <= point[1] and point[1] <= grid[1][1]

def findIntersection(grid1, grid2):
    ret = [(max(grid1[0][0], grid2[0][0]), max(grid1[0][1], grid2[0][1])),
           (min(grid1[1][0], grid2[1][0]), min(grid1[1][1], grid2[1][1]))]
    if ret[0][0] > ret[1][0] or ret[0][1] > ret[1][1]:
        return [(0, 0), (0, 0)]
    return ret

def ease(progress):
    return 1 if progress > 0.7 else (-2.04 * ((progress - 0.7) ** 2) + 1)

def ease2(progress):
    return progress ** 2

while framecnt < fps * 8:
    frame = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)
    frame[:] = (255, 255, 255)
    progress = framecnt / (float(fps) * 8)
    progress2 = (framecnt - 2 * fps) / (float(fps) * 6)
    for i in range(4):
        p = (positions[i][0] + int(directions[i][0] * images[i].shape[1] * ease(progress)),
             positions[i][1] + int(directions[i][1] * images[i].shape[0] * ease(progress)))
        intersec = findIntersection([p,
                                     (p[0] + images[i].shape[1] - 1,
                                      p[1] + images[i].shape[0] - 1)],
                                     grids[i])
        frame[intersec[0][1]:intersec[1][1],
              intersec[0][0]:intersec[1][0]] = grayimages[i][intersec[0][1] - p[1]:intersec[1][1] - p[1],
                                                             intersec[0][0] - p[0]:intersec[1][0] - p[0]]
        if framecnt > fps * 2:
            p = (positions[i][0] + int(directions[i][0] * images[i].shape[1] * ease(progress2)),
                 positions[i][1] + int(directions[i][1] * images[i].shape[0] * ease(progress2)))
            intersec = findIntersection([p,
                                         (p[0] + images[i].shape[1] - 1,
                                          p[1] + images[i].shape[0] - 1)],
                                         grids[i])
            frame[intersec[0][1]:intersec[1][1],
                  intersec[0][0]:intersec[1][0]] = images[i][intersec[0][1] - p[1]:intersec[1][1] - p[1],
                                                             intersec[0][0] - p[0]:intersec[1][0] - p[0]]

    if framecnt > fps * 5.5 and framecnt < fps * 6:
        flashamount = int(255 * ease2((fps * 0.25 - abs(framecnt - fps * 5.75)) / (fps * 0.25)))
        flash = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)
        flash[:] = (flashamount, flashamount, flashamount)
        frame = cv2.add(frame, flash)
    
    for c in range(0,3):
        frame[:,:,c] =  overlay[:,:,c] * (overlay[:,:,3]/255.0) +  frame[:,:,c] * (1.0 - overlay[:,:,3]/255.0)

    if framecnt > fps * 5.5:
        progress_overlay = (framecnt - 5.5 * fps) / (float(fps) * 2.5)
        p = (position_overlay[0] + int(direction_overlay[0] * overlay2.shape[1] * 1.5 * ease(progress_overlay)),
             position_overlay[1] + int(direction_overlay[1] * overlay2.shape[0] * 1.5 * ease(progress_overlay)))
        intersec = findIntersection([p,
                                     (p[0] + overlay2.shape[1] - 1,
                                      p[1] + overlay2.shape[0] - 1)],
                                     [(0,0), (1920, 1080)])
        for c in range(0,3):
            frame[intersec[0][1]:intersec[1][1],
                  intersec[0][0]:intersec[1][0],
                  c] = overlay2[intersec[0][1] - p[1]:intersec[1][1] - p[1],
                                intersec[0][0] - p[0]:intersec[1][0] - p[0],
                                c] * (overlay2[intersec[0][1] - p[1]:intersec[1][1] - p[1],
                                               intersec[0][0] - p[0]:intersec[1][0] - p[0],
                                               3] / 255.0) + frame[intersec[0][1]:intersec[1][1],
                                                             intersec[0][0]:intersec[1][0],
                                                             c] * (1.0 - overlay2[intersec[0][1] - p[1]:intersec[1][1] - p[1],
                                                                   intersec[0][0] - p[0]:intersec[1][0] - p[0],
                                                                   3] / 255.0)
    
    output.write(frame)
    framecnt += 1

output.release()
