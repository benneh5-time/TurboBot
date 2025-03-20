from PIL import Image, ImageDraw, ImageFont
import textwrap

def overlay_text_on_image(image_path, output_path, text):
    image = Image.open(image_path)
    width, height = image.size
    overlay_height = int(height * 0.2)  # 20% of the image height

    # Create a black overlay
    overlay = Image.new("RGB", (width, overlay_height), (0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Use a larger font size and ensure font is loaded correctly
    font_size = 80  # Increased font size (double the previous 40)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=font_size)
    except IOError:
        font = ImageFont.load_default()  # Fallback if the font file is missing

    # Wrap text to fit the overlay width
    max_chars_per_line = width // (font_size // 2)  # Adjust based on font size
    wrapped_text = "\n".join(textwrap.wrap(text, width=max_chars_per_line))

    # Draw text on the black overlay
    draw.text((0, 0), wrapped_text, fill=(255, 255, 255), font=font)

    # Paste overlay onto image
    image.paste(overlay, (0, height - overlay_height))
    image.save(output_path)
    print(f"Image saved to {output_path}")
