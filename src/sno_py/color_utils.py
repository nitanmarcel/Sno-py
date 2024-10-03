import colorsys


def adjust_color_brightness(hex_color: str, factor: float) -> str:
    hex_color = hex_color.lstrip("#")
    rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    hue, light, sat = colorsys.rgb_to_hls(*[x / 255.0 for x in rgb])
    light = max(min(light * factor, 1.0), 0.0)
    rgb = colorsys.hls_to_rgb(hue, light, sat)
    return "#{:02x}{:02x}{:02x}".format(
        int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
    )
