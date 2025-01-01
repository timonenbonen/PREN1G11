import math
import os

import cv2
import numpy as np
from matplotlib import pyplot as plt

# Read the image
script_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(script_dir, "test_50a.jpg")
# image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
# Convert the image to the HSV color space
hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Check if the image was successfully loaded
if image is None:
    print("Error: Could not read the image.")
else:
    # Image dimensions
    h, w = image.shape[:2]

    # Field of view parameters
    diagonal_fov = 120  # degrees
    horizontal_fov = 102  # degrees
    vertical_fov = 67  # degrees

    # Calculate focal lengths
    focal_length_x = w / (2 * np.tan(np.radians(horizontal_fov) / 2))
    focal_length_y = h / (2 * np.tan(np.radians(vertical_fov) / 2))

    # Camera matrix
    camera_matrix = np.array(
        [[focal_length_x, 0, w / 2], [0, focal_length_y, h / 2], [0, 0, 1]],
        dtype=np.float32,
    )

    # Distortion coefficients (example values, replace with your own)
    dist_coeffs = np.array([-0.2, 0.1, 0, 0], dtype=np.float32)
    # Undistort the image
    undistorted_image = cv2.undistort(image, camera_matrix, dist_coeffs)

    # Display the original and undistorted images in a subplot
    plt.figure(figsize=(10, 10))

    plt.subplot(121)
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title("Original Image")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(122)
    plt.imshow(cv2.cvtColor(undistorted_image, cv2.COLOR_BGR2RGB))
    plt.title("Undistorted Image")
    plt.xticks([])
    plt.yticks([])

    plt.show()
    # Display the resized original (distorted) image

    # HUGH
    dst = cv2.Canny(image, 50, 200, None, 3)

    # Copy edges to the images that will display the results in BGR
    cdst = cv2.cvtColor(dst, cv2.COLOR_GRAY2BGR)
    cdstP = np.copy(cdst)

    lines = cv2.HoughLines(dst, 1, np.pi / 180, 150, None, 0, 0)

    if lines is not None:
        for i in range(0, len(lines)):
            rho = lines[i][0][0]
            theta = lines[i][0][1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            pt1 = (int(x0 + 1000 * (-b)), int(y0 + 1000 * (a)))
            pt2 = (int(x0 - 1000 * (-b)), int(y0 - 1000 * (a)))
            cv2.line(cdst, pt1, pt2, (0, 0, 255), 3, cv2.LINE_AA)

    linesP = cv2.HoughLinesP(dst, 1, np.pi / 180, 50, None, 50, 10)

    if linesP is not None:
        for i in range(0, len(linesP)):
            l = linesP[i][0]
            cv2.line(cdstP, (l[0], l[1]), (l[2], l[3]), (0, 0, 255), 3, cv2.LINE_AA)

    edges = cv2.Canny(image, 100, 200, None, 3)

    plt.figure(figsize=(10, 10))

    plt.subplot(221)
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title("Original Image")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(222)
    plt.imshow(cv2.cvtColor(cdst, cv2.COLOR_BGR2RGB))
    plt.title("Detected Lines - Standard Hough")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(223)
    plt.imshow(cv2.cvtColor(cdstP, cv2.COLOR_BGR2RGB))
    plt.title("Detected Lines - Probabilistic Hough")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(224)
    plt.imshow(edges, cmap="gray")
    plt.title("Edge Image")
    plt.xticks([])
    plt.yticks([])

    plt.show()

    lower_white = np.array([0, 0, 220])
    upper_white = np.array([180, 50, 255])

    # Create a mask for the white color
    mask_white = cv2.inRange(hsv_image, lower_white, upper_white)
    # Erode the mask to remove noise
    kernel = np.ones((5, 5), np.uint8)
    eroded_mask = cv2.erode(mask_white, kernel, iterations=2)

    # Dilate the mask to restore the eroded parts
    dilated_mask = cv2.dilate(eroded_mask, kernel, iterations=1)

    plt.figure(figsize=(10, 10))

    plt.subplot(221)
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title("Original Image")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(222)
    plt.imshow(mask_white, cmap="gray")
    plt.title("White Line Detection")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(223)
    plt.imshow(eroded_mask, cmap="gray")
    plt.title("Eroded Mask")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(224)
    plt.imshow(dilated_mask, cmap="gray")
    plt.title("Dilated Mask")
    plt.xticks([])
    plt.yticks([])

    plt.show()

    # Run line detection on the new masked images
    dst_masked = cv2.Canny(dilated_mask, 50, 200, None, 3)

    # Copy edges to the images that will display the results in BGR
    cdst_masked = cv2.cvtColor(dst_masked, cv2.COLOR_GRAY2BGR)
    cdstP_masked = np.copy(cdst_masked)

    lines_masked = cv2.HoughLines(dst_masked, 1, np.pi / 180, 150, None, 0, 0)

    if lines_masked is not None:
        for i in range(0, len(lines_masked)):
            rho = lines_masked[i][0][0]
            theta = lines_masked[i][0][1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            pt1 = (int(x0 + 1000 * (-b)), int(y0 + 1000 * (a)))
            pt2 = (int(x0 - 1000 * (-b)), int(y0 - 1000 * (a)))
            cv2.line(cdst_masked, pt1, pt2, (0, 0, 255), 3, cv2.LINE_AA)

    linesP_masked = cv2.HoughLinesP(dst_masked, 1, np.pi / 180, 50, None, 50, 10)

    if linesP_masked is not None:
        for i in range(0, len(linesP_masked)):
            l = linesP_masked[i][0]
            cv2.line(
                cdstP_masked, (l[0], l[1]), (l[2], l[3]), (0, 0, 255), 3, cv2.LINE_AA
            )

    plt.figure(figsize=(10, 10))

    plt.subplot(221)
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title("Original Image")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(222)
    plt.imshow(cv2.cvtColor(cdst_masked, cv2.COLOR_BGR2RGB))
    plt.title("Detected Lines - Standard Hough on Masked Image")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(223)
    plt.imshow(cv2.cvtColor(cdstP_masked, cv2.COLOR_BGR2RGB))
    plt.title("Detected Lines - Probabilistic Hough on Masked Image")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(224)
    plt.imshow(dst_masked, cmap="gray")
    plt.title("Edge Image on Masked Image")
    plt.xticks([])
    plt.yticks([])

    plt.show()

    # Using Hough Line Transform with different parameters
    lines_new = cv2.HoughLines(dst, 1, np.pi / 360, 100, None, 0, 0)

    cdst_new = np.copy(cdst)
    if lines_new is not None:
        for i in range(0, len(lines_new)):
            rho = lines_new[i][0][0]
            theta = lines_new[i][0][1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            pt1 = (int(x0 + 1000 * (-b)), int(y0 + 1000 * (a)))
            pt2 = (int(x0 - 1000 * (-b)), int(y0 - 1000 * (a)))
            cv2.line(cdst_new, pt1, pt2, (0, 255, 0), 3, cv2.LINE_AA)

    linesP_new = cv2.HoughLinesP(dst, 1, np.pi / 360, 30, None, 30, 5)

    cdstP_new = np.copy(cdstP)
    if linesP_new is not None:
        for i in range(0, len(linesP_new)):
            l = linesP_new[i][0]
            cv2.line(cdstP_new, (l[0], l[1]), (l[2], l[3]), (0, 255, 0), 3, cv2.LINE_AA)

    plt.figure(figsize=(10, 10))

    plt.subplot(221)
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title("Original Image")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(222)
    plt.imshow(cv2.cvtColor(cdst_new, cv2.COLOR_BGR2RGB))
    plt.title("Detected Lines - Standard Hough with New Params")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(223)
    plt.imshow(cv2.cvtColor(cdstP_new, cv2.COLOR_BGR2RGB))
    plt.title("Detected Lines - Probabilistic Hough with New Params")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(224)
    plt.imshow(dst, cmap="gray")
    plt.title("Edge Image")
    plt.xticks([])
    plt.yticks([])

    plt.show()

    def on_trackbar(val):
        lower_orange[0] = cv2.getTrackbarPos("Lower H", "Orange Cone Detection")
        lower_orange[1] = cv2.getTrackbarPos("Lower S", "Orange Cone Detection")
        lower_orange[2] = cv2.getTrackbarPos("Lower V", "Orange Cone Detection")
        upper_orange[0] = cv2.getTrackbarPos("Upper H", "Orange Cone Detection")
        upper_orange[1] = cv2.getTrackbarPos("Upper S", "Orange Cone Detection")
        upper_orange[2] = cv2.getTrackbarPos("Upper V", "Orange Cone Detection")
        mask_orange = cv2.inRange(hsv_image, lower_orange, upper_orange)
        # Resize the mask to fit the original image dimensions
        height, width = image.shape[:2]
        new_dim = (int(width * 0.4), int(height * 0.4))
        mask_orange_resized = cv2.resize(
            mask_orange, new_dim, interpolation=cv2.INTER_AREA
        )
        cv2.imshow("Orange Cone Detection", mask_orange_resized)
        # cv2.imshow("Orange Cone Detection", mask_orange)

    lower_orange = np.array([14, 43, 240])
    upper_orange = np.array([30, 255, 255])

    cv2.namedWindow("Orange Cone Detection")
    cv2.resizeWindow("Orange Cone Detection", 1270, 734)
    cv2.createTrackbar(
        "Lower H", "Orange Cone Detection", lower_orange[0], 180, on_trackbar
    )
    cv2.createTrackbar(
        "Lower S", "Orange Cone Detection", lower_orange[1], 255, on_trackbar
    )
    cv2.createTrackbar(
        "Lower V", "Orange Cone Detection", lower_orange[2], 255, on_trackbar
    )
    cv2.createTrackbar(
        "Upper H", "Orange Cone Detection", upper_orange[0], 180, on_trackbar
    )
    cv2.createTrackbar(
        "Upper S", "Orange Cone Detection", upper_orange[1], 255, on_trackbar
    )
    cv2.createTrackbar(
        "Upper V", "Orange Cone Detection", upper_orange[2], 255, on_trackbar
    )
    on_trackbar(0)  # Initial call to update the mask
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Create a mask for the orange color
    mask_orange = cv2.inRange(hsv_image, lower_orange, upper_orange)

    # Erode the mask to remove noise
    eroded_mask_orange = cv2.erode(mask_orange, kernel, iterations=1)

    # Dilate the mask to restore the eroded parts
    dilated_mask_orange = cv2.dilate(eroded_mask_orange, kernel, iterations=25)

    # Find contours in the mask
    contours, _ = cv2.findContours(
        dilated_mask_orange, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    # Draw contours on the original image
    image_with_contours = np.copy(image)
    for contour in contours:
        if cv2.contourArea(contour) > 100:  # Filter small contours
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(image_with_contours, (x, y), (x + w, y + h), (0, 255, 0), 2)

    plt.figure(figsize=(10, 10))

    plt.subplot(221)
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title("Original Image")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(222)
    plt.imshow(mask_orange, cmap="gray")
    plt.title("Orange Cone Mask")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(223)
    plt.imshow(dilated_mask_orange, cmap="gray")
    plt.title("Eroded and Dilated Mask")
    plt.xticks([])
    plt.yticks([])

    plt.subplot(224)
    plt.imshow(cv2.cvtColor(image_with_contours, cv2.COLOR_BGR2RGB))
    plt.title("Detected Orange Cone")
    plt.xticks([])
    plt.yticks([])

    plt.show()
