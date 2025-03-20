from PIL import Image, ImageDraw, ImageFont
import textwrap

def overlay_text_on_image(image_path, output_path, text):
    image = Image.open(image_path)
    width, height = image.size
    overlay_height = int(height * 0.2)  # 20% of the image height

    # Create a black overlay
    overlay = Image.new("RGB", (width, overlay_height), (0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Increase font size
    max_font_size = 44 #int(overlay_height * 0.4)  # 40% of overlay height
    min_font_size = 10
    font_size = max_font_size

    while font_size > min_font_size:
        try:
            font = ImageFont.truetype("arial.ttf", size=font_size)
        except IOError:
            font = ImageFont.load_default()
        
        # Wrap text based on width
        max_chars_per_line = width // 2
        wrapped_text = "\n".join(textwrap.wrap(text, width=max_chars_per_line * 2))

        # Measure text size
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # If text fits, break
        if text_height <= overlay_height:
            break
        font_size -= 2

    # Draw text without alignment adjustments
    draw.text((0, 0), wrapped_text, fill=(255, 255, 255), font=font)

    # Paste overlay onto image
    image.paste(overlay, (0, height - overlay_height))
    image.save(output_path)
    print(f"Image saved to {output_path}")
