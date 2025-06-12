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
    
    # A4サイズ (mm -> pixel at 300dpi) - 基準サイズとして使用
    A4_WIDTH_MM = 210
    A4_HEIGHT_MM = 297
    DPI = 300
    
    # アスペクト比 4:5 (幅:高さ)
    ASPECT_RATIO = (4, 5)
    
    def __init__(self):
        self.a4_width = int(self.A4_WIDTH_MM * self.DPI / 25.4)
        self.a4_height = int(self.A4_HEIGHT_MM * self.DPI / 25.4)
        self.margin = int(10 * self.DPI / 25.4)  # 10mm margin
        self.info_height = int(35 * self.DPI / 25.4)  # 35mm for info section
        self.image_info_gap = int(8 * self.DPI / 25.4)  # 8mm gap between images and info
        
    def create_sheet(self, 
                    processed_images: List[Tuple[Image.Image, int]],
                    film_format: FilmFormat,
                    info: Dict[str, str]) -> Image.Image:
        """コンタクトシートを作成（4:5アスペクト比）"""
        
        # 画像配置の計算
        layout_info = self._calculate_layout(processed_images, film_format)
        
        # 4:5アスペクト比でのサイズ計算
        sheet_width, sheet_height = self._calculate_optimal_size(layout_info)
        
        # 背景画像作成
        sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
        draw = ImageDraw.Draw(sheet)
        
        # 画像を配置
        self._place_images(sheet, processed_images, film_format, layout_info, sheet_width)
        
        # 情報セクションを追加
        self._add_info_section(sheet, draw, info, sheet_width, sheet_height)
        
        return sheet
    
    def _calculate_layout(self, processed_images: List[Tuple[Image.Image, int]], 
                         film_format: FilmFormat) -> Dict:
        """レイアウト情報を計算"""
        images_per_row = film_format.images_per_row
        num_images = len(processed_images)
        
        # A4幅を基準にサムネイルサイズを計算
        available_width = self.a4_width - (2 * self.margin)
        thumb_width = available_width // images_per_row - 10  # 画像間の余白
        
        # アスペクト比に基づいて高さを計算
        aspect_w, aspect_h = film_format.aspect_ratio
        thumb_height = int(thumb_width * aspect_h / aspect_w)
        
        # 必要な行数を計算
        rows_needed = (num_images + images_per_row - 1) // images_per_row
        
        # 実際に必要なコンテンツサイズ
        content_width = images_per_row * thumb_width + (images_per_row - 1) * 10
        content_height = rows_needed * thumb_height + (rows_needed - 1) * 10
        
        return {
            'thumb_width': thumb_width,
            'thumb_height': thumb_height,
            'rows_needed': rows_needed,
            'images_per_row': images_per_row,
            'content_width': content_width,
            'content_height': content_height
        }
    
    def _calculate_optimal_size(self, layout_info: Dict) -> Tuple[int, int]:
        """4:5アスペクト比を維持した最適サイズを計算"""
        # 必要な最小高さ
        min_height = (2 * self.margin +           # 上下マージン
                     layout_info['content_height'] +  # 画像エリア
                     self.image_info_gap +        # 画像と情報の間隔
                     self.info_height)            # 情報エリア
        
        # 必要な最小幅
        min_width = layout_info['content_width'] + 2 * self.margin
        
        # 4:5のアスペクト比を維持
        # 幅から高さを決める場合
        height_from_width = int(min_width * self.ASPECT_RATIO[1] / self.ASPECT_RATIO[0])
        # 高さから幅を決める場合  
        width_from_height = int(min_height * self.ASPECT_RATIO[0] / self.ASPECT_RATIO[1])
        
        # より大きい方を採用（コンテンツが収まるように）
        if height_from_width >= min_height:
            # 幅ベースのサイズが適している
            final_width = min_width
            final_height = height_from_width
        else:
            # 高さベースのサイズが必要
            final_width = width_from_height
            final_height = min_height
        
        # A4サイズを超えないように制限
        if final_width > self.a4_width or final_height > self.a4_height:
            # A4サイズを4:5に調整
            a4_height_for_ratio = int(self.a4_width * self.ASPECT_RATIO[1] / self.ASPECT_RATIO[0])
            if a4_height_for_ratio <= self.a4_height:
                final_width = self.a4_width
                final_height = a4_height_for_ratio
            else:
                final_height = self.a4_height
                final_width = int(self.a4_height * self.ASPECT_RATIO[0] / self.ASPECT_RATIO[1])
        
        return final_width, final_height
    
    def _place_images(self, sheet: Image.Image, 
                     processed_images: List[Tuple[Image.Image, int]],
                     film_format: FilmFormat, layout_info: Dict, sheet_width: int) -> None:
        """画像を配置（中央寄せ）"""
        current_row = 0
        current_col = 0
        
        thumb_width = layout_info['thumb_width']
        thumb_height = layout_info['thumb_height']
        images_per_row = layout_info['images_per_row']
        content_width = layout_info['content_width']
        
        # 中央寄せのための開始位置
        start_x = (sheet_width - content_width) // 2
        
        for img, number in processed_images:
            # サムネイル作成
            thumbnail = ImageProcessor().create_thumbnail(img, (thumb_width, thumb_height))
            thumbnail = ImageProcessor().add_number_overlay(thumbnail, number)
            
            # 位置計算
            x = start_x + current_col * (thumb_width + 10)
            y = self.margin + current_row * (thumb_height + 10)
            
            # 画像貼り付け
            sheet.paste(thumbnail, (x, y))
            
            # 次の位置へ
            current_col += 1
            if current_col >= images_per_row:
                current_col = 0
                current_row += 1
    
    def _add_info_section(self, sheet: Image.Image, draw: ImageDraw.Draw, 
                         info: Dict[str, str], sheet_width: int, sheet_height: int) -> None:
        """情報セクションを追加（適切な余白付き）"""
        # フォント設定
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 
                                    int(14 * self.DPI / 72))  # 14pt
            font_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 
                                         int(16 * self.DPI / 72), index=1)  # Bold
        except:
            font = ImageFont.load_default()
            font_bold = font
        
        # 情報エリアの開始位置（下部から逆算）
        info_y = sheet_height - self.margin - self.info_height
        
        # 区切り線（情報エリアの上端に描画）
        line_y = info_y
        draw.line([(self.margin, line_y), 
                  (sheet_width - self.margin, line_y)], 
                 fill='black', width=2)
        
        # 情報を描画（線から適切な余白を空けて）
        y_offset = line_y + 15  # 線から15ピクセル下
        line_height = int(18 * self.DPI / 72)  # 行間
        
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
        right_x = sheet_width // 2
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
            
            draw.text(((sheet_width - text_width) // 2, film_y), 
                     film_text, 
                     font=font_bold, fill='black')
    
    def save_as_jpeg(self, sheet: Image.Image, output_path: str, quality: int = 95) -> None:
        """JPEG形式で保存"""
        sheet.save(output_path, 'JPEG', quality=quality, dpi=(self.DPI, self.DPI))
    
    def save_as_png(self, sheet: Image.Image, output_path: str) -> None:
        """PNG形式で保存"""
        sheet.save(output_path, 'PNG', dpi=(self.DPI, self.DPI))
    
    def save_as_pdf(self, sheets: List[Image.Image], output_path: str) -> None:
        """PDF形式で保存（4:5アスペクト比対応）"""
        c = canvas.Canvas(output_path, pagesize=A4)
        
        for sheet in sheets:
            # PILイメージをPDFに変換
            img_buffer = io.BytesIO()
            sheet.save(img_buffer, format='PNG', dpi=(self.DPI, self.DPI))
            img_buffer.seek(0)
            
            # 実際のシートサイズを取得
            sheet_width_pt = sheet.width * 72 / self.DPI
            sheet_height_pt = sheet.height * 72 / self.DPI
            
            # A4サイズに収まるようにスケール計算
            a4_width, a4_height = A4
            scale_x = a4_width / sheet_width_pt
            scale_y = a4_height / sheet_height_pt
            scale = min(scale_x, scale_y, 1.0)  # 拡大はしない
            
            final_width = sheet_width_pt * scale
            final_height = sheet_height_pt * scale
            
            # 中央配置
            x = (a4_width - final_width) / 2
            y = (a4_height - final_height) / 2
            
            c.drawImage(ImageReader(img_buffer), x, y, 
                       width=final_width, height=final_height)
            c.showPage()
        
        c.save()
