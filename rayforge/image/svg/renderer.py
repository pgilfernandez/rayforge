import logging
import warnings
from typing import Optional, TYPE_CHECKING
from xml.etree import ElementTree as ET
from ..base_renderer import Renderer

logger = logging.getLogger(__name__)

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    import pyvips

if TYPE_CHECKING:
    pass


class SvgRenderer(Renderer):
    """Renders SVG data."""

    def render_base_image(
        self,
        data: bytes,
        width: int,
        height: int,
        **kwargs,
    ) -> Optional[pyvips.Image]:
        """
        Renders raw SVG data to a pyvips Image by setting its pixel dimensions.
        Expects data to be pre-trimmed for content.
        """
        if not data:
            return None
        try:
            # Modify SVG dimensions for the loader to render at target size
            root = ET.fromstring(data)
            root.set("width", f"{width}px")
            root.set("height", f"{height}px")
            root.set("preserveAspectRatio", "none")

            svg_bytes = ET.tostring(root)

            # Prefer CairoSVG because bundled libvips may lack SVG support on
            # macOS. Fall back to svgload_buffer if available.
            try:
                import cairosvg

                png_bytes = cairosvg.svg2png(
                    bytestring=svg_bytes,
                    output_width=width,
                    output_height=height,
                )
                logger.debug("Rendered SVG via CairoSVG fallback path.")
                return pyvips.Image.pngload_buffer(
                    png_bytes, access=pyvips.Access.RANDOM
                )
            except ImportError:
                logger.error("CairoSVG is not available for SVG rendering.")
            except (pyvips.Error, ValueError, TypeError, Exception) as e:
                logger.error(
                    "CairoSVG fallback failed to render SVG: %s",
                    e,
                    exc_info=True,
                )

            try:
                svg_loader = getattr(pyvips.Image, "svgload_buffer")
            except AttributeError:
                svg_loader = None

            if svg_loader:
                logger.debug("Rendered SVG via libvips svgload_buffer.")
                return svg_loader(svg_bytes)

            logger.error(
                "No SVG renderer succeeded (CairoSVG/libvips unavailable)."
            )
        except (pyvips.Error, ET.ParseError, ValueError, TypeError) as e:
            logger.error(f"Failed to render SVG: {e}", exc_info=True)
            return None


SVG_RENDERER = SvgRenderer()
