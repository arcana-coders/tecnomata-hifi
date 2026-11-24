"""Generador de ícono retro estilo Sony Hi-Fi 80s/90s para escritorio Windows."""
from PIL import Image, ImageDraw

def create_hifi_icon(size=256):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    scale = size / 256.0

    def s(val):
        return int(val * scale)

    # 1. Sombra exterior
    draw.rounded_rectangle(
        [s(14), s(22), s(242), s(246)],
        radius=s(28),
        fill=(0, 0, 0, 90)
    )
    draw.rounded_rectangle(
        [s(16), s(20), s(240), s(242)],
        radius=s(26),
        fill=(0, 0, 0, 140)
    )

    # 2. Chassis principal (Gunmetal con bisel metálico)
    draw.rounded_rectangle(
        [s(18), s(18), s(238), s(238)],
        radius=s(24),
        fill=(60, 62, 72, 255),
        outline=(95, 98, 115, 255),
        width=max(1, s(2))
    )
    draw.rounded_rectangle(
        [s(21), s(21), s(235), s(235)],
        radius=s(22),
        fill=(22, 23, 28, 255)
    )

    # 3. Bocinas laterales
    for spk_x1, spk_x2 in [(s(28), s(72)), (s(184), s(228))]:
        draw.rounded_rectangle(
            [spk_x1, s(48), spk_x2, s(218)],
            radius=s(10),
            fill=(14, 15, 18, 255),
            outline=(45, 47, 56, 255),
            width=1
        )
        # Tweeter
        cx = (spk_x1 + spk_x2) // 2
        cy1 = s(86)
        r1 = s(16)
        draw.ellipse([cx - r1, cy1 - r1, cx + r1, cy1 + r1], fill=(28, 30, 36, 255), outline=(55, 57, 68, 255))
        draw.ellipse([cx - s(6), cy1 - s(6), cx + s(6), cy1 + s(6)], fill=(12, 13, 16, 255))

        # Woofer
        cy2 = s(160)
        r2 = s(22)
        draw.ellipse([cx - r2, cy2 - r2, cx + r2, cy2 + r2], fill=(26, 28, 34, 255), outline=(65, 68, 80, 255), width=max(1, s(1)))
        draw.ellipse([cx - s(9), cy2 - s(9), cx + s(9), cy2 + s(9)], fill=(255, 102, 0, 180)) # Naranja Sony
        draw.ellipse([cx - s(5), cy2 - s(5), cx + s(5), cy2 + s(5)], fill=(15, 15, 18, 255))

    # 4. Consola Central
    cen_x1, cen_x2 = s(78), s(178)

    # Header
    draw.rectangle([cen_x1, s(32), cen_x2, s(46)], fill=(18, 19, 24, 255))
    draw.text((cen_x1 + s(6), s(33)), "TECNO", fill=(240, 240, 245, 255))
    draw.text((cen_x1 + s(52), s(34)), "Hi-Fi", fill=(255, 102, 0, 255))

    # Display VFD
    vfd_y1, vfd_y2 = s(52), s(122)
    draw.rounded_rectangle(
        [cen_x1, vfd_y1, cen_x2, vfd_y2],
        radius=s(6),
        fill=(5, 10, 8, 255),
        outline=(30, 32, 40, 255),
        width=1
    )

    # Ecualizador gráfico VFD
    bars_x = cen_x1 + s(8)
    bar_w = max(2, s(5))
    gap = max(1, s(2))
    bar_heights = [18, 28, 42, 50, 44, 36, 48, 52, 40, 32, 22, 14]
    for i, bh in enumerate(bar_heights):
        bx = bars_x + i * (bar_w + gap)
        if bx + bar_w >= cen_x2 - s(4):
            break
        by2 = vfd_y2 - s(8)
        by1 = by2 - max(3, s(bh // 1.4))

        draw.rectangle([bx, by1, bx + bar_w, by2], fill=(0, 255, 170, 230))
        draw.rectangle([bx, by1 - max(1, s(2)), bx + bar_w, by1], fill=(0, 220, 255, 255))

    # Scanlines VFD sutiles
    step = max(2, s(3))
    for y in range(vfd_y1 + 1, vfd_y2 - 1, step):
        draw.line([cen_x1 + 1, y, cen_x2 - 1, y], fill=(0, 0, 0, 50))

    # 5. Compartimento de Cassette
    deck_y1, deck_y2 = s(130), s(192)
    draw.rounded_rectangle(
        [cen_x1, deck_y1, cen_x2, deck_y2],
        radius=s(6),
        fill=(14, 15, 18, 255),
        outline=(40, 42, 52, 255),
        width=1
    )

    c_win_x1, c_win_x2 = cen_x1 + s(8), cen_x2 - s(8)
    draw.rounded_rectangle(
        [c_win_x1, deck_y1 + s(6), c_win_x2, deck_y2 - s(6)],
        radius=s(4),
        fill=(8, 8, 10, 255),
        outline=(255, 102, 0, 100),
        width=1
    )

    # Carretes de cinta
    r_cy = (deck_y1 + deck_y2) // 2
    r_rad = max(4, s(14))
    for rcx in [cen_x1 + s(28), cen_x2 - s(28)]:
        draw.ellipse([rcx - r_rad, r_cy - r_rad, rcx + r_rad, r_cy + r_rad], fill=(24, 25, 30, 255), outline=(200, 200, 210, 200))
        draw.ellipse([rcx - max(1, s(5)), r_cy - max(1, s(5)), rcx + max(1, s(5)), r_cy + max(1, s(5))], fill=(255, 255, 255, 255))

    draw.line([cen_x1 + s(28), r_cy + s(10), cen_x2 - s(28), r_cy + s(10)], fill=(40, 25, 15, 255), width=max(1, s(3)))

    # 6. Botones inferiores
    btn_y1, btn_y2 = s(200), s(224)
    btn_w = max(3, s(18))
    btn_gap = max(1, s(5))
    btn_start_x = cen_x1 + s(5)
    colors = [(60, 62, 70), (255, 102, 0), (60, 62, 70), (60, 62, 70)]

    for i in range(4):
        bx = btn_start_x + i * (btn_w + btn_gap)
        draw.rounded_rectangle(
            [bx, btn_y1, bx + btn_w, btn_y2],
            radius=max(1, s(3)),
            fill=colors[i],
            outline=(80, 82, 95, 255),
            width=1
        )

    return img

if __name__ == "__main__":
    master = create_hifi_icon(256)
    master.save("icon.png", "PNG")

    # Generar tamaños usando downsampling de alta calidad LANCZOS
    sizes = [256, 128, 64, 48, 32, 16]
    layers = []
    for sz in sizes:
        if sz == 256:
            layers.append(master)
        else:
            layers.append(master.resize((sz, sz), Image.Resampling.LANCZOS))

    layers[0].save("icon.ico", format="ICO", sizes=[(s, s) for s in sizes])
    print("icon.png y icon.ico generados exitosamente.")
