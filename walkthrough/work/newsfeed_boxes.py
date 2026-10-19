# Finds the news-feed image placeholders (flat #F8F8FA panels) in a phone frame.
# Returns visible row spans plus the panel's full extent, inferring a clipped top/bottom from the known panel height.
import numpy as np

PH = np.array([248, 248, 250])

def placeholder_mask(a):
    return (np.abs(a - PH).sum(2) <= 4)

def find_boxes(a, min_rows=60):
    """a: HxWx3 int array (996x2160 phone frame). Returns list of dicts with x0,x1,vis_y0,vis_y1."""
    m = placeholder_mask(a)
    H, W = m.shape
    # rows where most of a wide band is placeholder-grey (the centre icon interrupts only the middle)
    band = m[:, 40:W - 40]
    rowfrac = band.mean(1)
    rows = rowfrac > 0.55
    boxes, y = [], 0
    while y < H:
        if rows[y]:
            y0 = y
            while y < H and rows[y]: y += 1
            y1 = y
            if y1 - y0 >= min_rows:
                # width from a row clear of the centre icon: the run's first or last rows
                cols = m[y0:min(y0 + 12, y1)].all(0) | m[max(y1 - 12, y0):y1].all(0)
                xs = np.where(cols)[0]
                span = (xs.min(), xs.max())
                boxes.append(dict(x0=int(span[0]), x1=int(span[1]) + 1, vis_y0=y0, vis_y1=y1))
        else:
            y += 1
    return boxes
