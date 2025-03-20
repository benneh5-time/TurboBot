from PIL import Image, ImageDraw, ImageFont
import textwrap

def overlay_text_on_image(image_path, output_path, text):
    image = Image.open(image_path)
    width, height = image.size
    overlay_height = int(height * 0.3)  # Bottom 30% of the image

    # Create black overlay
    overlay = Image.new("RGB", (width, overlay_height), (0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Use installed DejaVu Sans font
    font_path = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"
    
    # Start with a large font and scale down if needed
    max_font_size = int(overlay_height * 0.4)  # 40% of overlay height
    font_size = max_font_size

    while font_size > 10:  # Minimum font size threshold
        font = ImageFont.truetype(font_path, size=font_size)
        max_chars_per_line = width // (font_size // 2)

        # Wrap text to fit within width
        wrapped_text = "\n".join(textwrap.wrap(text, width=max_chars_per_line))

        # Measure text size
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # Check if it fits within the overlay
        if text_height <= overlay_height:
            break  # Stop reducing font size if it fits

        font_size -= 2  # Reduce font size and retry

    # Draw text on overlay (left-aligned, no centering)
    draw.text((10, 10), wrapped_text, fill=(255, 255, 255), font=font)

    # Paste overlay onto image
    image.paste(overlay, (0, height - overlay_height))
    image.save(output_path)

    print(f"Image saved to {output_path}")
