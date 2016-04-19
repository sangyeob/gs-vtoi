import numpy
import imageio
import time

cap = imageio.get_reader("test_media/20160325_214851.mp4", 'ffmpeg')
st = time.time()
count = 0
init = False
try:
	for i, image in enumerate(cap):
	        if not init:
	                board = image
	                print image.shape[:2]
	                init = True
	        if count % 5 == 1:
	                board = numpy.hstack((board, image))
	        count += 1
	        print count,
except:
	pass
print
imageio.imwrite("static/img.tif", board)
print 'elapsed time:', time.time() - st, '(s)'