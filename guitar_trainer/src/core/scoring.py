def get_tier_info(pct):
    if pct is None:
        return None, None
    tiers = [
        (10, "Poopoo Tier", (139, 69, 19)),
        (20, "Casserole Tier", (169, 169, 169)),
        (30, "Fausse Note Tier", (255, 69, 0)),
        (40, "Apprenti Sourd Tier", (218, 165, 32)),
        (50, "Garage Band Tier", (70, 130, 180)),
        (60, "Ok Tier", (144, 238, 144)),
        (70, "Feu de Camp Tier", (255, 140, 0)),
        (80, "Local Hero Tier", (0, 191, 255)),
        (90, "Virtuose-ish Tier", (186, 85, 211)),
        (97.5, "Guitar Hero Tier", (255, 215, 0)),
        (99, "God Tier", (0, 255, 255)),
        (101, "Ultimate God Tier", (255, 255, 255))
    ]
    for threshold, name, color in tiers:
        if pct <= threshold:
            return name, color
    return tiers[-1][1], tiers[-1][2]
