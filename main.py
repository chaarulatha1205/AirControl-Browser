import cv2
import mediapipe as mp
import subprocess
import time

# ---------- Setup ----------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.8,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("ERROR: Camera not accessible")
    exit()

URLS = {
    "Left_1": "https://www.miniclip.com/games/en/",
    "Left_2": "https://www.youtube.com/",
    "Left_3": "https://www.wikipedia.org/",
    "Left_4": "https://www.reddit.com/",
    "Left_5": "https://www.netflix.com/",

    "Right_1": "https://www.google.com/search?q=google+gemini",
    "Right_2": "https://chat.openai.com/",
    "Right_3": "https://www.bbc.com/news",
    "Right_4": "https://www.instagram.com/",
    "Right_5": "https://www.linkedin.com/"
}

opened_links = set()
gesture_hold = {}
HOLD_TIME = 1.0


def count_fingers(lm, hand):
    fingers = []

    # Thumb
    if hand == "Right":
        fingers.append(lm[4].x < lm[3].x)
    else:
        fingers.append(lm[4].x > lm[3].x)

    # Other fingers
    for i in [8, 12, 16, 20]:
        fingers.append(lm[i].y < lm[i - 2].y)

    return sum(fingers)


def open_guest(url):
    if url in opened_links:
        return

    subprocess.Popen([
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--guest",
        url
    ])

    opened_links.add(url)


print("Camera opened successfully")

try:
    while True:
        success, frame = cap.read()
        if not success:
            print("ERROR: Frame not received")
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        now = time.time()

        try:
            result = hands.process(rgb)
        except Exception as e:
            print("MediaPipe error:", e)
            continue

        if result.multi_hand_landmarks:

            # ---------- TWO HANDS ----------
            if len(result.multi_hand_landmarks) == 2:
                counts = []

                for i in range(2):
                    lm = result.multi_hand_landmarks[i].landmark
                    label = result.multi_handedness[i].classification[0].label
                    counts.append(count_fingers(lm, label))

                if counts == [5, 5]:
                    opened_links.clear()
                    cv2.putText(
                        frame,
                        "ADMIN RESET SUCCESS",
                        (30, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 255),
                        3
                    )
                else:
                    cv2.putText(
                        frame,
                        "Multiple Hands - System Locked",
                        (30, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        3
                    )

            # ---------- SINGLE HAND ----------
            else:
                hand_lm = result.multi_hand_landmarks[0]
                label = result.multi_handedness[0].classification[0].label
                lm = hand_lm.landmark

                count = count_fingers(lm, label)
                key = f"{label}_{count}"

                mp_draw.draw_landmarks(
                    frame,
                    hand_lm,
                    mp_hands.HAND_CONNECTIONS
                )

                if key in URLS:
                    if key not in gesture_hold:
                        gesture_hold[key] = now
                    elif now - gesture_hold[key] >= HOLD_TIME:
                        open_guest(URLS[key])
                        gesture_hold.clear()

                cv2.putText(
                    frame,
                    f"{label} Hand - {count} Fingers",
                    (30, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )
        else:
            gesture_hold.clear()

        # ---------- ALWAYS SHOW FRAME ----------
        cv2.imshow("Enterprise Gesture Control System", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
