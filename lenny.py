from PIL import Image, ImageDraw, ImageFont
import textwrap

def overlay_text_on_image(image_path, output_path, text):  
    image = Image.open(image_path)  
    width, height = image.size  
    overlay_height = int(height * 0.2)  
    overlay = Image.new("RGB", (width, overlay_height), (0, 0, 0))  
    draw = ImageDraw.Draw(overlay)  

    # Find the largest font size that fits
    max_font_size = int(overlay_height * 0.2)  
    min_font_size = 10  
    font_size = max_font_size  

    while font_size > min_font_size:  
        try:
            font = ImageFont.truetype("arial.ttf", size=font_size)  
        except IOError:
            font = ImageFont.load_default()  
        
        max_chars_per_line = width // (font_size // 2)  
        wrapped_text = "\n".join(textwrap.wrap(text, width=max_chars_per_line))  
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)  
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]  

        # If text fits, break loop
        if text_width <= width and text_height <= overlay_height:  
            break  
        font_size -= 2  # Reduce font size and try again  

    # Center text
    text_x = (width - text_width) // 2  
    text_y = (overlay_height - text_height) // 2  

    # Draw text on black overlay
    draw.text((text_x, text_y), wrapped_text, fill=(255, 255, 255), font=font, align="center")  
    image.paste(overlay, (0, height - overlay_height))  
    image.save(output_path)  
    print(f"Image saved to {output_path}")