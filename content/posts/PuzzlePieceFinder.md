---
title: "Puzzle Piece Finder"
date: 2022-01-04T00:00:00Z
draft: false
author: "Dennis"
image: PuzzlePieceFinder/FindingLargestRectangle/BInnerRectanlge.png
---

There was this puzzle that had belonged to me for over a year now.

The following was its image:
![Puzzle](/images/PuzzlePieceFinder/Puzzle.png)

I scanned the image with my scanner. It didn’t quite fit into the scanner though because the box the image was printed onto was too big. That is why the image is blurred on the picture.

Because every piece of the puzzle looked almost completely the same, I planned on taking some OpenCV image recognition, a bit of python and some computing magic and throwing all these things into a program.

The result was a python based puzzle piece finder that actually worked:

Take a piece and scan it:
![Piece](/images/PuzzlePieceFinder/Piece.bmp)

After putting the picture into my project folder and running the script:
![Output](/images/PuzzlePieceFinder/Output.png)

The green rectangle shows the position where the piece would best fit based on its texture.

## How does it work?

First read the image from the file:

```python
piece_original_colored = cv2.imread(filepath)
```

The black border around the piece is only a small problem that can be fixed by cropping the image:
![Piece original](/images/PuzzlePieceFinder/OriginalCropped.png)

```python
piece_original_colored = piece_original_colored[25:920, 25:920]
height, width = piece_original_colored.shape[:2]
```

I then initiated some constants I’ll need later on:

```python
step_size = 15
padding = 30
shadow_padding_top = 0
x = 0
y = 0
max_background_saturation_std = 3
background_max_saturation = 5
percentage_of_difference_threshold = 0.05
```

Those constants contain some paddings, step sizes to speed up the process and not checking every single pixel in the image, starting values for x and y to prevent reference before assignment exceptions and a few thresholds that I figured would work best.

Next I needed to remove the unnecessary borders around the piece. I did that by checking all sides for their standard deviation in their saturation because the pieces actually contain a lot of color pigments whereas the background is a solid gray or white.

The code isn’t very optimized:

```python
# top
for top in range(0, height):
    saturations = []
    for x in range(0, width, step_size):
        cur_color = piece_original_colored[top, x]
        _, cur_saturation, _ = colorsys.rgb_to_hsv(cur_color[0], cur_color[1], cur_color[2])
        cur_saturation = int(cur_saturation*100)
        saturations.append(cur_saturation)
    if np.std(saturations) > max_background_saturation_std:
        break
# bottom
for bottom in range(height-1, top, -1):
    saturations = []
    for x in range(0, width, step_size):
        cur_color = piece_original_colored[bottom, x]
        _, cur_saturation, _ = colorsys.rgb_to_hsv(cur_color[0], cur_color[1], cur_color[2])
        cur_saturation = int(cur_saturation*100)
        saturations.append(cur_saturation)
    if np.std(saturations) > max_background_saturation_std:
        break
# left
for left in range(0, width):
    saturations = []
    for y in range(top, bottom, step_size):
        cur_color = piece_original_colored[y, left]
        _, cur_saturation, _ = colorsys.rgb_to_hsv(cur_color[0], cur_color[1], cur_color[2])
        cur_saturation = int(cur_saturation*100)
        saturations.append(cur_saturation)
    if np.std(saturations) > max_background_saturation_std:
        break
# right
for right in range(width-1, left, -1):
    saturations = []
    for y in range(top, bottom, step_size):
        cur_color = piece_original_colored[y, right]
        _, cur_saturation, _ = colorsys.rgb_to_hsv(cur_color[0], cur_color[1], cur_color[2])
        cur_saturation = int(cur_saturation*100)
        saturations.append(cur_saturation)
    if np.std(saturations) > max_background_saturation_std:
        break
piece_original_colored = piece_original_colored[top:bottom, left:right]
```

In a next step I also removed some shadows with OpenCV’s methods:

```python
# copy to not corrupt original
piece_marked = piece_original_colored.copy()

# get new width and height
height, width = piece_original_colored.shape[:2]

# remove shadows
rgb_planes = cv2.split(piece_marked)

result_norm_planes = []
for plane in rgb_planes:
    dilated_img = cv2.dilate(plane, np.ones((7,7), np.uint8))
    bg_img = cv2.medianBlur(dilated_img, 21)
    diff_img = 255 - cv2.absdiff(plane, bg_img)
    norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
    result_norm_planes.append(norm_img)

piece_marked = cv2.merge(result_norm_planes)
```

This part of my code is copied from Stack Overflow, so I am not sure what it does exactly.

![Piece shadows removed](/images/PuzzlePieceFinder/PieceRemovedShadows.png)

The next step was to find the parts of the image that actually contain the puzzle piece. First I subdivided the image into a grid:

```python
# create grid with step_size
grid = []
for x in range(step_size, width-step_size, step_size):
    column = []
    for y in range(step_size, height-step_size, step_size):
        column.append(False)
    grid.append(column)
```

![Piece grid](/images/PuzzlePieceFinder/Grid.png)

I defined a method that checks whether a cell contains a piece or not based on, again, its saturation values:

```python
def cell_contains_piece()
    y = step_size + row*step_size
    saturations = []
    for x2 in range(x-step_size, x+step_size):
        for y2 in range(y-step_size, y+step_size):
            cur_color = piece_original_colored[y2, x2]
            _, cur_saturation, _ = colorsys.rgb_to_hsv(cur_color[0], cur_color[1], cur_color[2])
            cur_saturation = int(cur_saturation*100)
            saturations.append(cur_saturation)
    number_of_different_colors = np.count_nonzero(np.asarray(saturations) > background_max_saturation)
    is_piece = number_of_different_colors/len(saturations) > percentage_of_difference_threshold
    return is_piece
```

The function actually works for an entire row at once:

```python
def row_contains_piece(x, column_index, grid, step_size, piece_original_colored, background_max_saturation, percentage_of_difference_threshold):
    row_length = len(grid[column_index])
    column = []
    for row in range(0, row_length):
        y = step_size + row*step_size
        saturations = []
        for x2 in range(x-step_size, x+step_size):
            for y2 in range(y-step_size, y+step_size):
                cur_color = piece_original_colored[y2, x2]
                _, cur_saturation, _ = colorsys.rgb_to_hsv(cur_color[0], cur_color[1], cur_color[2])
                cur_saturation = int(cur_saturation*100)
                saturations.append(cur_saturation)
        number_of_different_colors = np.count_nonzero(np.asarray(saturations) > background_max_saturation)
        is_piece = number_of_different_colors/len(saturations) > percentage_of_difference_threshold
        column.append(is_piece)
    return column, column_index
```

Because this algorithm is very inefficient but was the best and fastest I could come up with that works, I needed to speed up the process with multiprocessing:

```python
with concurrent.futures.ProcessPoolExecutor() as executor:
    results = []
    for column in range(0, len(grid)):
        x = step_size + column*step_size
        results.append(executor.submit(row_contains_piece, x, column, grid, step_size, piece_original_colored, background_max_saturation, percentage_of_difference_threshold))

    for f in concurrent.futures.as_completed(results):
        result, column = f.result()
        grid[column] = result
```

Because even after trying to remove the shadows caused by the scanner there still were some errors occurring at the top of the piece. I therefore removed the topmost row of cells and all the outer cells to prevent shadows from being recognized as part of the piece, and then I painted all the cells containing the piece black:

```python
# further removing shadows by removing two topmost cells from piece
for x in range(0, len(grid)):
    for y in range(0, len(grid[x])-1):
        if grid[x][y]:
            grid[x][y] = False
            grid[x][y-1] = False
            break
for column in range(1, len(grid)-1):
    for row in range(1, len(grid[column])-1):
        # get center coords
        x = step_size + column * step_size
        y = step_size + row * step_size

        # get amount of direct neighbour cells containing part of the piece
        neighbour_count = 0
        if grid[column-1][row]:
            neighbour_count += 1
        if grid[column][row-1]:
            neighbour_count += 1
        if grid[column+1][row]:
            neighbour_count += 1
        if grid[column][row+1]:
            neighbour_count += 1

        # fill cell black if part of piece and not at outer edge of piece
        if grid[column][row] and neighbour_count == 4:
            cv2.rectangle(piece_marked, (x-step_size, y-step_size), (x+step_size, y+step_size), (0, 0, 0), -1)
```

![Piece Marked](/images/PuzzlePieceFinder/PieceMarked.png)

The task now was to find a big rectangle inside the piece that I could feed to the template matching algorithm.

First I needed to find the center of the piece:

```python
piece_gray = cv2.cvtColor(piece_marked, cv2.COLOR_RGB2GRAY)

# find smallest surrounding
# top
for top in range(0, height, step_size):
    for x in range(0, width, step_size):
        pixel = piece_gray[top, x]
        if pixel == 0:
            break
    else:
        continue
    break
# bottom
for bottom in range(height-1, top, -step_size):
    for x in range(0, width, step_size):
        pixel = piece_gray[bottom, x]
        if pixel == 0:
            break
    else:
        continue
    break
# left
for left in range (0, width, step_size):
    for y in range(top, bottom, step_size):
        pixel = piece_gray[y, left]
        if pixel == 0:
            break
    else:
        continue
    break
# right
for right in range(width-1, left, -step_size):
    for y in range(top, bottom, step_size):
        pixel = piece_gray[y, right]
        if pixel == 0:
            break
    else:
        continue
    break

# get center of smallest surrounding
center = (int((left+right)/2), int((top+bottom)/2))
```

![Piece smallest surrounding](/images/PuzzlePieceFinder/SurroundingRectangle.png)

As of writing this post, I realize that this step is completely unnecessary after already cropping the piece.

Some further steps then include finding the largest centered square that fits into the piece, and then expanding that square in all directions to get a large rectangle:

```python
# get closest edge's distance
dist_vertical = bottom - center[1]
dist_horizontal = right - center[0]
closest_distance = dist_vertical if dist_vertical < dist_horizontal else dist_horizontal

# expand square from center until hits white or edge
not_black_pixel_found = False
for radius in range(10, closest_distance, step_size):
    # check top
    for x in range(center[0] - radius, center[0] + radius, step_size):
        pixel = piece_gray[center[1] - radius, x]
        if pixel != 0:
            not_black_pixel_found = True
            break
    # check left
    for y in range(center[1] - radius, center[1] + radius, step_size):
        pixel = piece_gray[y, center[0] - radius]
        if pixel != 0:
            not_black_pixel_found = True
            break
    # check bottom
    for x in range(center[0] - radius, center[0] + radius, step_size):
        pixel = piece_gray[center[1] + radius, x]
        if pixel != 0:
            not_black_pixel_found = True
            break
    # check right
    for y in range(center[1] - radius, center[1] + radius, step_size):
        pixel = piece_gray[y, center[0] + radius]
        if pixel != 0:
            print(pixel)
            not_black_pixel_found = True
            break
    if not_black_pixel_found:
        break

# expand other sides
# top
for inner_top in range(center[1] - radius, top, -step_size):
    for x in range(center[0]-radius, center[0] + radius, step_size):
        pixel = piece_gray[inner_top, x]
        if pixel != 0:
            inner_top += padding
            inner_top += shadow_padding_top
            break
    else:
        continue
    break
# bottom
for inner_bottom in range(center[1] + radius, bottom, step_size):
    for x in range(center[0]-radius, center[0] + radius, step_size):
        pixel = piece_gray[inner_bottom, x]
        if pixel != 0:
            inner_bottom -= padding
            break
    else:
        continue
    break
# left
for inner_left in range(center[0] - radius, left , -step_size):
    for y in range(inner_top, inner_bottom, step_size):
        pixel = piece_gray[y, inner_left]
        if pixel != 0:
            inner_left += padding
            break
    else:
        continue
    break
# right
for inner_right in range(center[0] + radius, right , step_size):
    for y in range(inner_top, inner_bottom, step_size):
        pixel = piece_gray[y, inner_right]
        if pixel != 0:
            inner_right -= padding
            break
    else:
        continue
    break
```

![Piece largest rectangle](/images/PuzzlePieceFinder/FindingLargestRectangle/AInnerSquare.png)
![Piece largest rectangle](/images/PuzzlePieceFinder/FindingLargestRectangle/BInnerRectangle.png)

Next step was to resize the image to the same size it would have in the picture of the puzzle. In my case, 40% would do the trick:

```python
def resize_image(img, scale_percent):
    height, width = img.shape[:2]
    height = int(height * scale_percent)
    width = int(width * scale_percent)
    dim = (width, height)
    resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
    # show preview
    if should_show_preview:
        cv2.imshow('preview', resized)
        cv2.setWindowTitle('preview', "cropped piece")
        cv2.waitKey(1)
    return resized

image = resize_image(image, 0.4)
```

![Piece cropped](/images/PuzzlePieceFinder/CroppedPiece.png)

Because of the blur in the original picture, the scanned piece would also need some blur to make the template matching work better:

```python
def motion_blur_image(img):
    size = 15

    # generating the kernel
    kernel_motion_blur = np.zeros((size, size))
    kernel_motion_blur[int((size-1)/2), :] = np.ones(size)
    kernel_motion_blur = kernel_motion_blur / size

    blurred = cv2.filter2D(img, -1, kernel_motion_blur)

    # show preview
    cv2.imshow('preview', blurred)
    cv2.setWindowTitle('preview', "blurred")
    cv2.waitKey(1)
    return blurred
```

![Piece blurred](/images/PuzzlePieceFinder/Blurred.png)

The last step in my project was to do some template matching for every of the 4 90° rotations of the piece:

```python
import cv2
import numpy as np
from numpy.core.fromnumeric import argsort
from colour import Color
import convertImage
import os
import time

import concurrent.futures

filepath = r'*******************************\PuzzleFindPieceProject\Piece.bmp'

# read puzzle image from file
original = cv2.imread(r'*******************************\PuzzleFindPieceProject\Puzzle.png')

# resize the image to fit on screen
width = original.shape[1]
height = original.shape[0]
ratio = width/height
target_height = 900
target_width = int(ratio*target_height)
dim = (target_width, target_height)

# initialize color gradient
red = Color("red")
gradient = list(red.range_to(Color("green"),100))
color_confidence_threshold = 0.7
# Read image from file
piece_image = convertImage.motion_blur_image(convertImage.resize_image(convertImage.get_cropped_image(filepath), 0.4))
# copy
puzzle_image = original.copy()

# remove file to make place for next image
os.rename(filepath, filepath.replace("Piece.bmp", r"old\Piece" + str(round(time.time()*1000)) + ".bmp"))

# for each 4 rotations:
with concurrent.futures.ProcessPoolExecutor() as executor:
    results = []
    for rotation_count in range(0, 4):
        f = executor.submit(get_best_matches, piece_image.copy(), puzzle_image)
        results.append(f)
        piece_image = cv2.rotate(piece_image, cv2.ROTATE_90_CLOCKWISE)

    for f in concurrent.futures.as_completed(results):
        rectangle, color_255_brg = f.result()
        cv2.rectangle(puzzle_image, rectangle[0], rectangle[1], color_255_brg, 10)

finish = time.perf_counter()

print("process took", round(finish-start, 2), "s")

cv2.imshow('output', cv2.resize(puzzle_image.copy(), dim, interpolation=cv2.INTER_AREA))
cv2.waitKey(1)
```

The template matching method was the following:

```python
# template matching
def get_best_matches(piece_image, puzzle_image):
    print("getting match")
    # template matching
    h, w = piece_image.shape[:-1]
    res = cv2.matchTemplate(puzzle_image, piece_image, cv2.TM_CCOEFF_NORMED)
    # get highest n values
    n = 5
    loc = np.unravel_index(np.argsort(-res, axis=None)[:n], res.shape)
    # draw rectangles
    for pt in zip(*loc[::-1]):  # Switch collumns and rows
        # set color depending on confidence
        confidence = res[pt[1]][pt[0]]
        if confidence - color_confidence_threshold < 0:
            gradient_index = 99
        else:
            gradient_index = 99 - int((confidence-color_confidence_threshold) / (1-color_confidence_threshold)*99)
        color = gradient[gradient_index]
        color_255 = tuple(i * 255 for i in color.rgb)
        color_255_brg = (color_255[2], color_255[0], color_255[1])

        # output
        rectangle = [pt, (pt[0] + w, pt[1] + h)]
        return rectangle, color_255_brg
```

I again used multiprocessing to speed up the entire process from a minute to about 11.5 seconds.

The result was markings on the puzzle image for the best matching spots for every rotation of the piece:

![Output](/images/PuzzlePieceFinder/Output.png)

As you can see, my algorithm worked and found the correct spot for the piece in the bottom left corner.

I also added the quality of life color gradient from red to green to show how good the match is. Furthermore, I automated the process of putting the picture into my projects directory and removing it after running my algorithm.

In the end, I only needed to press the scan button on my scanner and wait for 20 seconds to find the piece’s location. This project sped up puzzling so much that I finished the puzzle that I had been working on for a year in just 2 days.
