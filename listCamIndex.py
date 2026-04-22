import cv2

for i in range(10):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if cap.isOpened():
        ok, frame = cap.read()
        print(f"Index {i}: OPEN" + (" (reads frames)" if ok else " (opens but no frames)"))
        
        # If frames are available, show them
        if ok and frame is not None:
            cv2.imshow(f"Camera {i}", frame)
            cap.release()
    else:
        print(f"Index {i}: not available")

print("\nPress any key to close all windows...")
cv2.waitKey(0)
cv2.destroyAllWindows()