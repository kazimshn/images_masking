import cv2
import tkinter as tk
from tkinter import filedialog, colorchooser, simpledialog, messagebox
import os
import numpy as np
from PIL import Image

# Global değişkenler
rect_start = None
rect_end = None
cropping = False
selected_region = None
mask_color = (0, 0, 0)  # Varsayılan: Siyah
text_to_add = None
text_color = (255, 255, 255)  # Varsayılan: Beyaz
font_scale = 1
font_thickness = 2
max_width = 1200  # Pencere boyutunu aşmaması için maksimum genişlik
max_height = 800  # Maksimum yükseklik

# OpenCV'nin UTF-8 destekleyen yazı fontu
font = cv2.FONT_HERSHEY_SIMPLEX

def select_files():
    file_paths = filedialog.askopenfilenames(filetypes=[("JPEG dosyaları", "*.jpg;*.jpeg")])
    return list(file_paths)

def choose_color():
    global mask_color
    color_code = colorchooser.askcolor(title="Maske Rengini Seç")[0]
    if color_code:
        mask_color = (int(color_code[2]), int(color_code[1]), int(color_code[0]))  # RGB'den BGR'ye çevirme

def get_text():
    global text_to_add, text_color, font_scale, font_thickness
    text_to_add = simpledialog.askstring("Giriş", "Eklemek istediğiniz metni girin (boş bırakabilirsiniz):")
    if text_to_add:
        text_color_code = colorchooser.askcolor(title="Yazı Rengini Seç")[0]
        if text_color_code:
            text_color = (int(text_color_code[2]), int(text_color_code[1]), int(text_color_code[0]))  # RGB'den BGR'ye çevirme
        font_scale = simpledialog.askfloat("Giriş", "Yazı boyutunu girin (varsayılan 1):", minvalue=0.5, maxvalue=5.0) or 1
        font_thickness = simpledialog.askinteger("Giriş", "Yazı kalınlığını girin (varsayılan 2):", minvalue=1, maxvalue=10) or 2

def resize_image(image):
    height, width = image.shape[:2]
    if width > max_width or height > max_height:
        scale = min(max_width / width, max_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        return cv2.resize(image, (new_width, new_height)), scale
    return image, 1

def draw_rectangle(event, x, y, flags, param):
    global rect_start, rect_end, cropping, selected_region
    
    if event == cv2.EVENT_LBUTTONDOWN:
        rect_start = (x, y)
        cropping = True
    
    elif event == cv2.EVENT_LBUTTONUP:
        rect_end = (x, y)
        cropping = False
        selected_region = (rect_start[0], rect_start[1], rect_end[0], rect_end[1])

def select_mask_area(image_path):
    global selected_region
    image = cv2.imread(image_path)
    image_resized, scale = resize_image(image)
    clone = image_resized.copy()
    cv2.namedWindow("Bölge Seç", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Bölge Seç", draw_rectangle)
    
    while True:
        temp_image = clone.copy()
        if rect_start and rect_end:
            cv2.rectangle(temp_image, rect_start, rect_end, (0, 255, 0), 2)
        
        cv2.imshow("Bölge Seç", temp_image)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord("q"):
            break
    
    cv2.destroyAllWindows()
    
    if selected_region:
        return tuple(int(x / scale) for x in selected_region)
    return None

def mask_images(image_paths, region):
    output_dir = "masked_images"
    os.makedirs(output_dir, exist_ok=True)
    
    for image_path in image_paths:
        image = cv2.imread(image_path)
        x1, y1, x2, y2 = region
        cv2.rectangle(image, (x1, y1), (x2, y2), mask_color, -1)
        
        if text_to_add:
            text_size = cv2.getTextSize(text_to_add, font, font_scale, font_thickness)[0]
            text_x = x1 + (x2 - x1 - text_size[0]) // 2
            text_y = y1 + (y2 - y1 + text_size[1]) // 2
            image = cv2.putText(image, text_to_add, (text_x, text_y), font, font_scale, text_color, font_thickness, lineType=cv2.LINE_AA)
        
        output_path = os.path.join(output_dir, os.path.basename(image_path))
        cv2.imwrite(output_path, image)
        
        # Orijinal DPI değerini korumak için PIL kullanarak yeniden kaydetme
        original_img = Image.open(image_path)
        dpi = original_img.info.get("dpi", (300, 300))  # Varsayılan olarak 300 DPI kullan
        pil_image = Image.open(output_path)
        pil_image.save(output_path, dpi=dpi)
    
    print(f"Maskeleme işlemi tamamlandı. Dosyalar '{output_dir}' klasörüne kaydedildi.")
    messagebox.showinfo("Tamamlandı", "Maskeleme işlemi başarıyla tamamlandı! Dosyalar 'masked_images' klasörüne kaydedildi.")

def main():
    root = tk.Tk()
    root.withdraw()
    
    print("Maskeleme işlemi için resimleri seçin")
    image_paths = select_files()
    if not image_paths:
        print("Seçili dosya bulunamadı!")
        return
    
    print("İlk resimde maskeleme bölgesini belirleyin")
    region = select_mask_area(image_paths[0])
    if not region:
        print("Maskeleme bölgesi belirlenmedi!")
        return
    
    print("Maske rengini seçin")
    choose_color()
    
    print("Üzerine yazı eklemek ister misiniz? (Opsiyonel)")
    get_text()
    
    print("Maskeleme işlemi uygulanıyor...")
    mask_images(image_paths, region)
    print("İşlem tamamlandı!")
    
if __name__ == "__main__":
    main()
