from PIL import Image, ImageDraw, ImageFont
import textwrap

def overlay_text_on_image(image_path, output_path, text):
    image = Image.open(image_path)
    width, height = image.size
    overlay_height = int(height * 0.3)
    
    overlay = Image.new("RGB", (width, overlay_height), (0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Maximum and minimum font sizes
    max_font_size = int(overlay_height * 0.2)
    min_font_size = 10
    font_size = max_font_size

    # Try different font sizes to fit text
    while font_size > min_font_size:
        try:
            font = ImageFont.truetype("arial.ttf", size=font_size)
        except IOError:
            font = ImageFont.load_default()
        
        max_chars_per_line = width // (font_size // 2)
        wrapped_text = "\n".join(textwrap.wrap(text, width=max_chars_per_line))
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # If text fits the overlay, stop reducing font size
        if text_height <= overlay_height:
            break
        font_size -= 2  # Decrease font size if it doesn’t fit

    # Set the left margin
    text_x = int(width * 0.05)  # Small padding from the left
    text_y = (overlay_height - text_height) // 2  # Vertically centered

    # Draw text on black overlay
    draw.text((text_x, text_y), wrapped_text, fill=(255, 255, 255), font=font, align="left")
    image.paste(overlay, (0, height - overlay_height))
    image.save(output_path)
