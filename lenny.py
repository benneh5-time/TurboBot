from PIL import Image, ImageDraw, ImageFont
import textwrap

def overlay_text_on_image(image_path, output_path, text):
    image = Image.open(image_path)
    width, height = image.size
    overlay_height = int(height * 0.2)
    
    # Create a black overlay for the bottom 30% of the image
    overlay = Image.new("RGB", (width, overlay_height), (0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Use a fixed font size
    font_size = int(overlay_height * 0.35)  # Adjust as needed
    try:
        font = ImageFont.truetype("arial.ttf", size=font_size)
    except IOError:
        font = ImageFont.load_default()

    # Calculate max characters per line and wrap text
    max_chars_per_line = width // (font_size // 2)  # Rough estimate of how many characters fit
    wrapped_text = "\n".join(textwrap.wrap(text, width=max_chars_per_line))

    # Calculate text position
    text_x = int(width * 0.05)  # 5% left margin
    text_y = int((overlay_height - draw.textbbox((0, 0), wrapped_text, font=font)[3]) / 2)  # Center vertically

    # Draw text onto overlay
    draw.text((text_x, text_y), wrapped_text, fill=(255, 255, 255), font=font, align="left")

    # Paste overlay onto image
    image.paste(overlay, (0, height - overlay_height))
    image.save(output_path)
