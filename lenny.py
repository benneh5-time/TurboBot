from PIL import Image, ImageDraw, ImageFont
import textwrap

def overlay_text_on_image(image_path, output_path, text):
    image = Image.open(image_path)
    width, height = image.size
    overlay_height = int(height * 0.2)  # Bottom 20% of the image

    # Create black overlay
    overlay = Image.new("RGB", (width, overlay_height), (0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Use installed DejaVu Sans font
    font_path = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"
    font_size = 80  # Adjust as needed
    font = ImageFont.truetype(font_path, size=font_size)

    # Wrap text to fit overlay width
    max_chars_per_line = width // (font_size // 2)
    wrapped_text = "\n".join(textwrap.wrap(text, width=max_chars_per_line))

    # Draw text on overlay without alignment
    draw.text((10, 10), wrapped_text, fill=(255, 255, 255), font=font)

    # Paste overlay onto image
    image.paste(overlay, (0, height - overlay_height))
    image.save(output_path)

    print(f"Image saved to {output_path}")
