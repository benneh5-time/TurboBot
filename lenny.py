from PIL import Image, ImageDraw, ImageFont
import textwrap


def overlay_text_on_image(image_path, output_path, text):
    image = Image.open(image_path)
    width, height = image.size
    overlay_height = int(height * 0.2)  # 20% of the image height

    # Create a black overlay
    overlay = Image.new("RGB", (width, overlay_height), (0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Use a fixed font size
    font_size = 40  # Fixed font size, no scaling
    try:
        font = ImageFont.truetype("arial.ttf", size=font_size)
    except IOError:
        font = ImageFont.load_default()

    # Draw text on black overlay with no alignment or scaling
    draw.text((0, 0), text, fill=(255, 255, 255), font=font)

    # Paste overlay onto image
    image.paste(overlay, (0, height - overlay_height))
    image.save(output_path)
    print(f"Image saved to {output_path}")