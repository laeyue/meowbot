import random
import string
from PIL import Image, ImageDraw, ImageFont
import os

def generate_captcha():
    """Generate a CAPTCHA image and return the text and path."""
    # Create the captcha directory if it doesn't exist
    os.makedirs('data/captcha_images', exist_ok=True)
    
    # Generate random text
    text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Create image
    width = 200
    height = 80
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Add noise
    for _ in range(1000):
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        draw.point((x, y), fill='gray')
    
    # Add text
    try:
        font = ImageFont.truetype('arial.ttf', 36)
    except:
        font = ImageFont.load_default()
    
    # Draw text with random position and rotation
    for i, char in enumerate(text):
        x = 20 + i * 30
        y = random.randint(10, 30)
        angle = random.randint(-20, 20)
        draw.text((x, y), char, font=font, fill='black', angle=angle)
    
    # Save image
    filename = f'data/captcha_images/{text}.png'
    image.save(filename)
    
    return text, filename

def verify_captcha(user_input, captcha_text):
    """Verify if the user input matches the CAPTCHA text."""
    return user_input.upper() == captcha_text 