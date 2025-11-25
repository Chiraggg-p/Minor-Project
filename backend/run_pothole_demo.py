# run_pothole_demo.py
# This is a proof-of-concept script to demonstrate the core AI 
# technology for pothole detection, as described in the project plan.
# This script is standalone and not connected to the main backend.

from ultralytics import YOLO
import os

# --- Configuration ---
# Use the local image file you just saved
IMAGE_PATH = "pothole_test.jpg" 

# We are using a standard, pre-trained model for this PoC.
MODEL_NAME = "yolov8n.pt" 
# ---

def run_detection_demo():
    print(f"Loading AI model '{MODEL_NAME}'... (This may download it the first time)")
    
    # 1. Load the pre-trained YOLOv8 model
    model = YOLO(MODEL_NAME)

    # *** FIX 1: Changed IMAGE_URL to IMAGE_PATH ***
    print(f"Running object detection on local image: {IMAGE_PATH}")
    
    # 2. Run the model on the local image
    # 'conf=0.4' sets the confidence threshold to 40%
    # *** FIX 2: Changed IMAGE_URL to IMAGE_PATH ***
    results = model.predict(IMAGE_PATH, conf=0.4)

    # 3. Save the resulting image
    result = results[0] # Get the first result
    
    # Define where to save the output file
    output_directory = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_directory, "pothole_detection_result.jpg")

    # Save the image with the detection boxes drawn on it
    result.save(filename=output_path)

    print("\n--- Detection Results ---")
    
    # 4. Print the detected objects and their confidence
    names = result.names
    for box in result.boxes:
        class_name = names[box.cls[0].item()]
        confidence = box.conf[0].item() * 100 # as a percentage
        
        # This general model might find 'pothole', 'crack', or just 'person', 'car'
        # Let's print anything it's confident about
        if confidence > 50:
             print(f"Detected: {class_name} (Confidence: {confidence:.2f}%)")

    print(f"\nSuccess! Result image saved to: {output_path}")
    print("This demonstrates the technology's capability for the 'Static Hazard Map' feature.")

# This line makes the script run when you call it from the terminal
if __name__ == "__main__":
    run_detection_demo()