from ..utils import pil2tensor
from ..utils import here, comfy_dir
from ..log import log
import folder_paths
from pathlib import Path
import shutil
import csv


class SmartStep:
    """Utils to control the steps start/stop of the KAdvancedSampler in percentage"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "step": (
                    "INT",
                    {"default": 20, "min": 1, "max": 10000, "step": 1},
                ),
                "start_percent": (
                    "INT",
                    {"default": 0, "min": 0, "max": 100, "step": 1},
                ),
                "end_percent": (
                    "INT",
                    {"default": 0, "min": 0, "max": 100, "step": 1},
                ),
            }
        }

    RETURN_TYPES = ("INT", "INT", "INT")
    RETURN_NAMES = ("step", "start", "end")
    FUNCTION = "do_step"
    CATEGORY = "mtb/conditioning"

    def do_step(self, step, start_percent, end_percent):
        start = int(step * start_percent / 100)
        end = int(step * end_percent / 100)

        return (step, start, end)


def install_default_styles(force=False):
    styles_dir = Path(folder_paths.base_path) / "styles"
    styles_dir.mkdir(parents=True, exist_ok=True)
    default_style = here / "styles.csv"
    dest_style = styles_dir / "default.csv"

    if force or not dest_style.exists():
        log.debug(f"Copying default style to {dest_style}")
        shutil.copy2(default_style.as_posix(), dest_style.as_posix())

    return dest_style


class StylesLoader:
    """Load csv files and populate a dropdown from the rows (à la A111)"""

    options = {}

    @classmethod
    def INPUT_TYPES(cls):
        if not cls.options:
            input_dir = Path(folder_paths.base_path) / "styles"
            if not input_dir.exists():
                install_default_styles()

            if not (files := [f for f in input_dir.iterdir() if f.suffix == ".csv"]):
                log.warn(
                    "No styles found in the styles folder, place at least one csv file in the styles folder at the root of ComfyUI (for instance ComfyUI/styles/mystyle.csv)"
                )

            for file in files:
                with open(file, "r", encoding="utf8") as f:
                    parsed = csv.reader(f)
                    for row in parsed:
                        log.debug(f"Adding style {row[0]}")
                        cls.options[row[0]] = (row[1], row[2])

        else:
            log.debug(f"Using cached styles (count: {len(cls.options)})")

        return {
            "required": {
                "style_name": (list(cls.options.keys()),),
            }
        }

    CATEGORY = "mtb/conditioning"

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "load_style"

    def load_style(self, style_name):
        return (self.options[style_name][0], self.options[style_name][1])


class TextToImage:
    """Utils to convert text to image using a font


    The tool looks for any .ttf file in the Comfy folder hierarchy.
    """

    fonts = {}

    def __init__(self):
        # - This is executed when the graph is executed, we could conditionaly reload fonts there
        pass

    @classmethod
    def CACHE_FONTS(cls):
        font_extensions = ["*.ttf", "*.otf", "*.woff", "*.woff2", "*.eot"]
        fonts = []

        for extension in font_extensions:
            fonts.extend(comfy_dir.glob(f"**/{extension}"))

        if not fonts:
            log.warn(
                "> No fonts found in the comfy folder, place at least one font file somewhere in ComfyUI's hierarchy"
            )
        else:
            log.debug(f"> Found {len(fonts)} fonts")

        for font in fonts:
            log.debug(f"Adding font {font}")
            cls.fonts[font.stem] = font.as_posix()

    @classmethod
    def INPUT_TYPES(cls):
        if not cls.fonts:
            cls.CACHE_FONTS()
        else:
            log.debug(f"Using cached fonts (count: {len(cls.fonts)})")
        return {
            "required": {
                "text": (
                    "STRING",
                    {"default": "Hello world!"},
                ),
                "font": ((sorted(cls.fonts.keys())),),
                "wrap": (
                    "INT",
                    {"default": 120, "min": 0, "max": 8096, "step": 1},
                ),
                "font_size": (
                    "INT",
                    {"default": 12, "min": 1, "max": 2500, "step": 1},
                ),
                "width": (
                    "INT",
                    {"default": 512, "min": 1, "max": 8096, "step": 1},
                ),
                "height": (
                    "INT",
                    {"default": 512, "min": 1, "max": 8096, "step": 1},
                ),
                # "position": (["INT"], {"default": 0, "min": 0, "max": 100, "step": 1}),
                "color": (
                    "COLOR",
                    {"default": "black"},
                ),
                "background": (
                    "COLOR",
                    {"default": "white"},
                ),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "text_to_image"
    CATEGORY = "mtb/generate"

    def text_to_image(
        self, text, font, wrap, font_size, width, height, color, background
    ):
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        font = self.fonts[font]
        font = ImageFont.truetype(font, font_size)
        if wrap == 0:
            wrap = width / font_size
        lines = textwrap.wrap(text, width=wrap)
        log.debug(f"Lines: {lines}")
        line_height = font.getsize("hg")[1]
        img_height = height  # line_height * len(lines)
        img_width = width  # max(font.getsize(line)[0] for line in lines)

        img = Image.new("RGBA", (img_width, img_height), background)
        draw = ImageDraw.Draw(img)
        y_text = 0
        for line in lines:
            width, height = font.getsize(line)
            draw.text((0, y_text), line, color, font=font)
            y_text += height

        # img.save(os.path.join(folder_paths.base_path, f'{str(uuid.uuid4())}.png'))
        return (pil2tensor(img),)


__nodes__ = [SmartStep, TextToImage, StylesLoader]
