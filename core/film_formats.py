from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Optional


class FilmType(Enum):
    """フィルムタイプの列挙型"""
    MM35_FULL = "35mm Full"
    MM35_HALF = "35mm Half"
    MM120_6X6 = "120mm 6x6"
    MM120_6X45 = "120mm 6x4.5"
    MM120_6X7 = "120mm 6x7"
    MM120_6X8 = "120mm 6x8"
    MM120_6X9 = "120mm 6x9"
    MM127_4X4 = "127mm 4x4"


@dataclass
class FilmFormat:
    """フィルムフォーマットの仕様"""
    type: FilmType
    aspect_ratio: Tuple[float, float]  # (width, height)
    images_per_row: int
    max_images: Optional[int]
    orientation: str  # 'landscape', 'portrait', 'square'
    force_rotation: bool  # 画像を強制的に回転させるか


# フィルムフォーマットの定義
FILM_FORMATS = {
    FilmType.MM35_FULL: FilmFormat(
        type=FilmType.MM35_FULL,
        aspect_ratio=(3, 2),
        images_per_row=6,
        max_images=36,
        orientation='landscape',
        force_rotation=True
    ),
    FilmType.MM35_HALF: FilmFormat(
        type=FilmType.MM35_HALF,
        aspect_ratio=(2, 3),
        images_per_row=12,
        max_images=72,
        orientation='portrait',
        force_rotation=True
    ),
    FilmType.MM120_6X6: FilmFormat(
        type=FilmType.MM120_6X6,
        aspect_ratio=(1, 1),
        images_per_row=3,
        max_images=12,
        orientation='square',
        force_rotation=False
    ),
    FilmType.MM120_6X45: FilmFormat(
        type=FilmType.MM120_6X45,
        aspect_ratio=(4.5, 6),
        images_per_row=3,
        max_images=16,
        orientation='portrait',
        force_rotation=True
    ),
    FilmType.MM120_6X7: FilmFormat(
        type=FilmType.MM120_6X7,
        aspect_ratio=(7, 6),
        images_per_row=3,
        max_images=10,
        orientation='landscape',
        force_rotation=True
    ),
    FilmType.MM120_6X8: FilmFormat(
        type=FilmType.MM120_6X8,
        aspect_ratio=(8, 6),
        images_per_row=3,
        max_images=9,
        orientation='landscape',
        force_rotation=True
    ),
    FilmType.MM120_6X9: FilmFormat(
        type=FilmType.MM120_6X9,
        aspect_ratio=(9, 6),
        images_per_row=3,
        max_images=8,
        orientation='landscape',
        force_rotation=True
    ),
    FilmType.MM127_4X4: FilmFormat(
        type=FilmType.MM127_4X4,
        aspect_ratio=(1, 1),
        images_per_row=3,
        max_images=12,
        orientation='square',
        force_rotation=False
    )
}


def get_film_format(film_type: FilmType) -> FilmFormat:
    """指定されたフィルムタイプのフォーマット情報を取得"""
    return FILM_FORMATS[film_type]