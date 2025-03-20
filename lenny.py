from PIL import Image, ImageDraw, ImageFont
import textwrap

def overlay_text_on_image(image_path, output_path, text):
    image = Image.open(image_path)
    width, height = image.size
    overlay_height = int(height * 0.3)
    
    overlay = Image.new("RGB", (width, overlay_height), (0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Maximum and minimum font sizes
    max_font_size = int(overlay_height * 0.25)  # Use 25% of overlay height as max font size
    min_font_size = 10
    font_size = max_font_size

    # Try different font sizes to fit text properly
    while font_size > min_font_size:
        try:
            font = ImageFont.truetype("arial.ttf", size=font_size)
        except IOError:
            font = ImageFont.load_default()
        
        # Calculate max width per line based on actual font size
        avg_char_width = font.getsize("A")[0]  # Width of a typical character
        max_chars_per_line = (width * 0.9) // avg_char_width  # Use 90% of width
        
        wrapped_text = "\n".join(textwrap.wrap(text, width=int(max_chars_per_line)))
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

        # If text fits within the overlay, break the loop
        if text_height <= overlay_height:
            break
        font_size -= 2  # Decrease font size and try again

    # Set position: left-aligned with padding
    text_x = int(width * 0.05)  # 5% padding from the left
    text_y = (overlay_height - text_height) // 2  # Center vertically in overlay

    # Draw text on black overlay
    draw.text((text_x, text_y), wrapped_text, fill=(255, 255, 255), font=font, align="left")
    image.paste(overlay, (0, height - overlay_height))
    image.save(output_path)