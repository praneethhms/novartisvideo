# Blurs the emergency contact's name and number in recA, following the bottom sheet as it slides.
# The contact line sits ~515px below the sheet's top edge on both SOS sheets.
# Usage: python3 blur_sos.py   (reads src/recA.mp4, writes src/recA_blur.mp4)
import glob, os, shutil, subprocess
import numpy as np
from PIL import Image, ImageFilter

tmp = 'peek/sosblur'
shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', 'src/recA.mp4', '-vf', 'fps=60', f'{tmp}/f%04d.png'], check=True)

def sheet_top(a):
    # the SOS sheets are near-black; find the first row (below the status area) where the left margin turns dark
    col = a[1200:, 40:80].mean(1)
    dark = np.where(col < 45)[0]
    return None if len(dark) == 0 else 1200 + int(dark[0])

for f in sorted(glob.glob(f'{tmp}/f*.png')):
    im = Image.open(f).convert('RGB')
    top = sheet_top(np.asarray(im.convert('L')).astype(int))
    if top is not None and top < 2700:
        y = top + 515
        box = (360, max(0, y - 70), 930, min(2796, y + 70))
        if box[3] > box[1]:
            im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(22)), box)
            im.save(f)
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-framerate', '60', '-i', f'{tmp}/f%04d.png',
                '-c:v', 'libx264', '-crf', '12', '-preset', 'fast', '-pix_fmt', 'yuv420p', 'src/recA_blur.mp4'], check=True)
shutil.rmtree(tmp)
print('ok')
