from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import List, Tuple, Optional
import os
from core.film_formats import FilmFormat, FilmType


class ImageProcessor:
    """画像処理クラス"""
    
    def __init__(self):
        self.images: List[Path] = []
        self.processed_images: List[Image.Image] = []
        
    def load_images(self, file_paths: List[str]) -> None:
        """画像ファイルを読み込み"""
        self.images = []
        for path in file_paths:
            if self._is_valid_image(path):
                self.images.append(Path(path))
        # ファイル名でソート
        self.images.sort(key=lambda x: x.name)
    
    def _is_valid_image(self, file_path: str) -> bool:
        """有効な画像ファイルかチェック"""
        valid_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
        return Path(file_path).suffix.lower() in valid_extensions
    
    def process_images(self, film_format: FilmFormat) -> List[Tuple[Image.Image, int]]:
        """フィルムフォーマットに応じて画像を処理"""
        self.processed_images = []
        
        for idx, img_path in enumerate(self.images, 1):
            img = Image.open(img_path)
            
            # RGB変換（RGBA等の場合）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 必要に応じて回転
            if film_format.force_rotation:
                img = self._rotate_image_if_needed(img, film_format.orientation)
            
            self.processed_images.append((img, idx))
        
        return self.processed_images
    
    def _rotate_image_if_needed(self, img: Image.Image, target_orientation: str) -> Image.Image:
        """必要に応じて画像を回転"""
        width, height = img.size
        is_landscape = width > height
        is_portrait = height > width
        is_square = width == height
        
        if target_orientation == 'landscape' and is_portrait:
            # 縦長を横長に（90度回転）
            return img.rotate(90, expand=True)
        elif target_orientation == 'portrait' and is_landscape:
            # 横長を縦長に（90度回転）
            return img.rotate(90, expand=True)
        
        return img
    
    def create_thumbnail(self, img: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """サムネイル作成（アスペクト比を維持）"""
        # アスペクト比を維持してリサイズ
        img_copy = img.copy()
        img_copy.thumbnail(size, Image.Resampling.LANCZOS)
        
        # 指定サイズの背景を作成（黒）
        background = Image.new('RGB', size, (0, 0, 0))
        
        # 中央に配置
        x = (size[0] - img_copy.width) // 2
        y = (size[1] - img_copy.height) // 2
        background.paste(img_copy, (x, y))
        
        return background
    
    def add_number_overlay(self, img: Image.Image, number: int, 
                          font_size: int = 20) -> Image.Image:
        """画像に番号を重ねる"""
        img_with_number = img.copy()
        draw = ImageDraw.Draw(img_with_number)
        
        # フォント設定（システムフォントを使用）
        try:
            # macOSの場合
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            # フォントが見つからない場合はデフォルト
            font = ImageFont.load_default()
        
        # 番号テキスト
        text = str(number)
        
        # テキストサイズを取得
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 左上に白い背景付きで番号を描画
        padding = 5
        x, y = padding, padding
        
        # 白い背景
        draw.rectangle(
            [x - 2, y - 2, x + text_width + 2, y + text_height + 2],
            fill='white',
            outline='black'
        )
        
        # 番号
        draw.text((x, y), text, font=font, fill='black')
        
        return img_with_number