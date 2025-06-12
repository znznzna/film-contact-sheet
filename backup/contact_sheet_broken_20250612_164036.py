from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import io
from core.film_formats import FilmFormat
from core.image_processor import ImageProcessor


class ContactSheet:
    """コンタクトシート生成クラス"""
    
    # A4サイズ (mm -> pixel at 300dpi)
    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297
    DPI = 300
    
    def __init__(self):
        self.width = int(self.A4_WIDTH_MM * self.DPI / 25.4)
        self.height = int(self.A4_HEIGHT_MM * self.DPI / 25.4)
        self.margin = int(10 * self.DPI / 25.4)  # 10mm margin
        self.info_height = int(35 * self.DPI / 25.4)  # 30mm for info section
        
    def create_sheet(self, 
                    processed_images: List[Tuple[Image.Image, int]],
                    film_format: FilmFormat,
                    info: Dict[str, str]) -> Image.Image:
        """コンタクトシートを作成"""
        
        # 背景画像作成（白）
        sheet = Image.new('RGB', (self.width, self.height), 'white')
        draw = ImageDraw.Draw(sheet)
        
        # 画像エリアの計算
        content_width = self.width - (2 * self.margin)
        content_height = self.height - (2 * self.margin) - self.info_height
        
        # サムネイルサイズの計算
        images_per_row = film_format.images_per_row
        thumb_width = content_width // images_per_row - 10  # 画像間の余白
        
        # アスペクト比に基づいて高さを計算
        aspect_w, aspect_h = film_format.aspect_ratio
        thumb_height = int(thumb_width * aspect_h / aspect_w)
        
        # 行数の計算
        max_rows = content_height // (thumb_height + 10)
        
        # 画像を配置
        current_row = 0
        current_col = 0
        
        for img, number in processed_images:
            if current_row >= max_rows:
                break  # ページに収まらない場合は次ページへ（現在は1ページのみ）
            
            # サムネイル作成
            thumbnail = ImageProcessor().create_thumbnail(img, (thumb_width, thumb_height))
            thumbnail = ImageProcessor().add_number_overlay(thumbnail, number)
            
            # 位置計算
            x = self.margin + current_col * (thumb_width + 10)
            y = self.margin + current_row * (thumb_height + 10)
            
            # 画像貼り付け
            sheet.paste(thumbnail, (x, y))
            
            # 次の位置へ
            current_col += 1
            if current_col >= images_per_row:
                current_col = 0
                current_row += 1
        
        # 情報セクションを追加
        self._add_info_section(sheet, draw, info)
        
        return sheet
    
        def _add_info_section(self, sheet: Image.Image, draw: ImageDraw.Draw, 
                         info: Dict[str, str]) -> None:
        """情報セクションを追加（レイアウト改善）"""
        # フォント設定
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 
                                    int(14 * self.DPI / 72))  # 14pt
            font_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 
                                         int(16 * self.DPI / 72), index=1)  # Bold
        except:
            font = ImageFont.load_default()
            font_bold = font
        
        # 情報エリアの開始位置
        info_y = self.height - self.margin - self.info_height
        
        # 区切り線
        draw.line([(self.margin, info_y), 
                  (self.width - self.margin, info_y)], 
                 fill='black', width=2)
        
        # 情報を描画
        y_offset = info_y + 15  # 上部余白を増加
        line_height = int(18 * self.DPI / 72)  # 行間を調整
        
        # 左側の情報
        left_items = []
        if info.get('date'):
            left_items.append(f"Date: {info['date']}")
        if info.get('location'):
            left_items.append(f"Location: {info['location']}")
        if info.get('developer'):
            left_items.append(f"Developer: {info['developer']}")
        
        for i, item in enumerate(left_items):
            draw.text((self.margin, y_offset + i * line_height), 
                     item, font=font, fill='black')
        
        # 右側の情報
        right_x = self.width // 2
        right_items = []
        if info.get('camera'):
            right_items.append(f"Camera: {info['camera']}")
        if info.get('lens'):
            right_items.append(f"Lens: {info['lens']}")
        
        for i, item in enumerate(right_items):
            draw.text((right_x, y_offset + i * line_height), 
                     item, font=font, fill='black')
        
        # フィルム名（中央下、他の情報から間隔を空ける）
        if info.get('film'):
            film_text = f"Film: {info['film']}"
            bbox = draw.textbbox((0, 0), film_text, font=font_bold)
            text_width = bbox[2] - bbox[0]
            
            # フィルム名の位置を他の情報から少し離す
            film_y = y_offset + max(len(left_items), len(right_items)) * line_height + int(8 * self.DPI / 72)
            
            draw.text(((self.width - text_width) // 2, film_y), 
                     film_text, 
                     font=font_bold, fill='black')

    def save_as_jpeg(self, sheet: Image.Image, output_path: str, quality: int = 95) -> None:
        """JPEG形式で保存"""
        sheet.save(output_path, 'JPEG', quality=quality, dpi=(self.DPI, self.DPI))
    
    def save_as_png(self, sheet: Image.Image, output_path: str) -> None:
        """PNG形式で保存"""
        sheet.save(output_path, 'PNG', dpi=(self.DPI, self.DPI))
    
    def save_as_pdf(self, sheets: List[Image.Image], output_path: str) -> None:
        """PDF形式で保存（複数ページ対応）"""
        c = canvas.Canvas(output_path, pagesize=A4)
        
        for sheet in sheets:
            # PILイメージをPDFに変換
            img_buffer = io.BytesIO()
            sheet.save(img_buffer, format='PNG', dpi=(self.DPI, self.DPI))
            img_buffer.seek(0)
            
            # A4サイズに合わせて描画
            c.drawImage(ImageReader(img_buffer), 0, 0, 
                       width=A4[0], height=A4[1])
            c.showPage()
        
        c.save()