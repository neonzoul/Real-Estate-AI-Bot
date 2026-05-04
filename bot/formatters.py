_INTENT_EMOJI = {"High": "🔥", "Medium": "🟡", "Low": "🔵"}


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
