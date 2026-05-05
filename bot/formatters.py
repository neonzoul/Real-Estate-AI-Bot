_INTENT_EMOJI = {"High": "🔥", "Medium": "🟡", "Low": "🔵"}

NO_MATCHES_MESSAGE = (
    "😔 No properties matched those requirements.\n"
    "Try adjusting the budget, location, or other criteria."
)


def _field(data: dict, key: str) -> str:
    value = data.get(key)
    if value is None or value == "":
        return "Not specified"
    return str(value)


def format_summary(data: dict) -> str:
    intent = _field(data, "intent_level")
    intent_emoji = _INTENT_EMOJI.get(intent, "🔥")

    lines = [
        "📋 *Lead Summary*",
        "",
        f"💰 *Budget:* {_field(data, 'budget')}",
        f"📍 *Location:* {_field(data, 'location')}",
        f"🏠 *Property Type:* {_field(data, 'property_type')}",
        f"📅 *Move-in Date:* {_field(data, 'move_in')}",
        f"{intent_emoji} *Intent Level:* {intent}",
        f"✅ *Recommended Next Step:* {_field(data, 'next_step')}",
    ]

    notes = data.get("notes") or []
    if notes:
        lines.append("")
        lines.append("💬 *Key Notes:*")
        for note in notes:
            lines.append(f"• {note}")

    return "\n".join(lines)


def _location_line(listing: dict) -> str:
    bts = listing.get("bts") or ""
    location = listing.get("location") or ""
    if bts:
        return f"📍 {bts} (BTS)"
    if location:
        return f"📍 {location}"
    return ""


def _price_line(listing: dict) -> str:
    parts: list[str] = []
    price = listing.get("price")
    if isinstance(price, int) and price > 0:
        parts.append(f"{price:,} THB/month")
    type_ = listing.get("type")
    if type_:
        parts.append(str(type_))
    size = listing.get("size_sqm")
    if isinstance(size, int) and size > 0:
        parts.append(f"{size} sqm")
    return f"💰 {' · '.join(parts)}" if parts else ""


def _features_line(listing: dict) -> str:
    features: list[str] = []
    if listing.get("pet_friendly"):
        features.append("Pet-friendly")
    if listing.get("parking"):
        features.append("Parking included")
    return f"✅ {' · '.join(features)}" if features else ""


def _details_line(listing: dict) -> str:
    parts: list[str] = []
    floor = listing.get("floor")
    if isinstance(floor, int) and floor > 0:
        parts.append(f"Floor {floor}")
    description = (listing.get("description") or "").strip()
    if description:
        parts.append(description)
    furnished = listing.get("furnished")
    if furnished:
        parts.append(f"{furnished} furnished")
    return f"📝 {' · '.join(parts)}" if parts else ""


def _format_match_block(rank: int, name: str, listing: dict | None) -> str:
    block_lines = [f"*{rank}. {name}*"]
    if listing is not None:
        for line in (
            _location_line(listing),
            _price_line(listing),
            _features_line(listing),
            _details_line(listing),
        ):
            if line:
                block_lines.append(line)
    return "\n".join(block_lines)


def format_matches(data: dict, listings: list[dict]) -> str:
    matches = data.get("matches") or []
    if not matches:
        return NO_MATCHES_MESSAGE

    by_name = {listing.get("name"): listing for listing in listings}

    count = len(matches)
    noun = "Property" if count == 1 else "Properties"
    lines = [f"🏠 *Results: {count} Matching {noun}*", ""]
    for index, match in enumerate(matches, start=1):
        rank = match.get("rank", index)
        name = match.get("name", "Unknown property")
        lines.append(_format_match_block(rank, name, by_name.get(name)))
        lines.append("")

    reply = (data.get("reply_message") or "").strip()
    if reply:
        lines.append("———")
        lines.append("💬 *Ready-to-send reply:*")
        lines.append("")
        lines.append(reply)

    return "\n".join(lines).rstrip()
