import os
import os.path
from pathlib import Path

import cv2


def crop(x, y, w, h, image_path=""):
	dirname = os.path.dirname(image_path)
	dirname = os.path.join(dirname, 'cropped')

	filename = os.path.basename(image_path)

	Path(dirname).mkdir(parents=True, exist_ok=True)
	if not isinstance(x, int):
		x = int(x)
	if not isinstance(y, int):
		y = int(y)
	if not isinstance(w, int):
		w = int(w)
	if not isinstance(h, int):
		h = int(h)

	if image_path != '' and w != 0 and h != 0:
		if image_path.endswith(".png") and not image_path.startswith("._"):  # bulletproofing against thumbnail files
			OutName = filename
			image = cv2.imread(image_path)
			cropped = image[y:y + h, x:x + w]
			cv2.imwrite(f"{dirname}/{OutName}", cropped)

		cv2.destroyAllWindows()
