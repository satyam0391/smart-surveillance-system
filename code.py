import RPi.GPIO as GPIO
import time
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# === Pin Setup ===
TRIG = 23
ECHO = 24
LED_PIN = 27  # Set the LED pin to GPIO 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(LED_PIN, GPIO.OUT)  # Set up the LED pin

# Email Configuration
EMAIL_ADDRESS = "sender@gmail.com"
EMAIL_PASSWORD = "sender app passward eg-vfgd dgjcb dhjd bdjd"
TO_EMAIL = "receiver@gmail.com"

def get_distance():
    GPIO.output(TRIG, False)
    time.sleep(0.01)
    
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    
    pulse_start = time.time()
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()  # Reset pulse_start for timeout checking
    
    pulse_end = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()  # Update pulse_end for timeout checking

    # Check if a valid pulse was detected
    if pulse_end - pulse_start <= 0:
        print("[ERROR] Timeout: No echo received")
        return -1  # Return error value if no pulse is detected

    duration = pulse_end - pulse_start
    distance = (duration * 34300) / 2  # cm
    return round(distance, 2)

def capture_and_send():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"captured_{now}.jpg"
    capture_command = f"libcamera-jpeg -o {filename} --width 640 --height 480 -n"

    print("[INFO] Capturing image...")
    if os.system(capture_command) != 0:
        print("[ERROR] Failed to capture image with libcamera.")
        return

    print(f"[INFO] Image captured: {filename}")

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg['Subject'] = "Security Alert: Image Captured"
    msg.attach(MIMEText("Unusual activity detected: A possible intruder has entered the home. Please review the attached photo immediately.", 'plain'))

    try:
        with open(filename, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)
    except Exception as e:
        print(f"[ERROR] Could not attach image: {e}")
        return

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, TO_EMAIL, msg.as_string())
        server.quit()
        print("[INFO] Email sent successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")

def blink_led(times):
    """Blink the LED a specified number of times."""
    for _ in range(times):
        GPIO.output(LED_PIN, GPIO.HIGH)  # Turn LED on
        time.sleep(0.2)  # 200ms on time
        GPIO.output(LED_PIN, GPIO.LOW)   # Turn LED off
        time.sleep(0.2)  # 200ms off time

# === Main Loop ===
try:
    while True:
        dist = get_distance()
        if dist == -1:
            print("[ERROR] Failed to measure distance")
        else:
            print(f"Distance: {dist} cm")
        
        if dist < 20:
            print("[INFO] Object detected, blinking LED...")
            blink_led(10)  # Blink LED 10 times
            
            capture_and_send()  # Capture image and send email
            time.sleep(10)  # Wait before next alert
            
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Measurement stopped by user")

finally:
    GPIO.cleanup() 


