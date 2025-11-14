import base64
import io
import mss
from PIL import Image
from openai import OpenAI

client = OpenAI()

def capture_screen():
    """Nimmt einen Screenshot mit mss und gibt ein PIL Image zurück."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Hauptmonitor
        sct_img = sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        return img

def image_to_base64(img: Image.Image) -> str:
    """Konvertiert PIL Image → Base64-String."""
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

def run_assistant():
    """Screenshot aufnehmen → KI schicken → Antwort zurückgeben."""
    print("📸 Screenshot wird aufgenommen...")
    img = capture_screen()
    b64_image = image_to_base64(img)

    print("🤖 KI wird abgefragt...")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Beschreibe den Screenshot."},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{b64_image}"
                    }
                ]
            }
        ]
    )

    output = response.choices[0].message["content"][0]["text"]
    print("\n===== KI ANTWORT =====\n")
    print(output)
    print("\n=======================\n")

if __name__ == "__main__":
    run_assistant()
