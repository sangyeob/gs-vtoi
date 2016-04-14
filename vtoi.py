import numpy
import cv2
import time

cap = cv2.VideoCapture("test_media/20160325_214851.mp4")
st = time.time()
count = 0
init = False
while True:
	success, image = cap.read()
	if not success:
		break
	if not init:
		board = cv2.resize(image, (0,0), fx=0.5, fy=0.5) 
		print image.shape[:2]
		init = True
	if count % 5 == 1:
		board = numpy.hstack((board, cv2.resize(image, (0,0), fx=0.5, fy=0.5)))
	count += 1
	print count,
print
print 'elapsed time:', time.time() - st, '(s)'
cv2.imwrite("a.png", board)
cv2.imwrite("a.jpg", board)