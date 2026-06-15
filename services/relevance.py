"""
Relevance filter — определяет является ли объявление именно тем товаром,
который ищет пользователь, а не аксессуаром/чехлом/запчастью к нему.

Логика:
1. Парсим поисковый запрос пользователя на токены (слова).
2. Заголовок объявления должен содержать ВСЕ ключевые токены запроса.
3. Если заголовок содержит слова-паразиты (аксессуары, запчасти) — отклоняем.
4. Проверяем что цена находится в реалистичном диапазоне для данного товара.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional


# ─── Словари мусора ───────────────────────────────────────────────────────────

# Слова, которые превращают объявление в аксессуар/запчасть
ACCESSORY_WORDS = {
    # Защита
    "чехол", "чохол", "case", "cover", "bumper", "бампер",
    "стекло", "скло", "плівка", "пленка", "film", "захисне",
    "захисний", "защитное", "протектор", "protector", "tempered",
    # Зарядка / кабели
    "кабель", "кабель", "cable", "зарядка", "зарядний", "charger",
    "адаптер", "adapter", "блок", "usb", "lightning", "type-c",
    "powerbank", "павербанк",
    # Запчасти
    "запчасти", "запчастини", "дисплей", "display", "экран", "екран",
    "батарея", "акумулятор", "battery", "динамік", "динамик",
    "камера", "module", "модуль", "flex", "шлейф", "разъем",
    # Аксессуары
    "тримач", "держатель", "holder", "підставка", "подставка",
    "ремінець", "ремешок", "strap", "band",
    "наушники", "навушники", "earphones", "airpods",
    # Прочее
    "книга", "журнал", "курс", "навчання", "обучение",
    "наклейка", "sticker",
}

# Слова срочности (для буста скора)
URGENCY_WORDS = {
    "срочно", "срочна", "терміново", "торг", "торгуюсь",
    "переїзд", "переезд", "не користуюсь", "не пользуюсь",
    "продам швидко", "потрібно продати", "нужно продать",
    "уступлю", "знижка", "скидка",
}

# Слова комплектности (для буста скора)
COMPLETENESS_WORDS = {
    "коробка", "коробці", "box", "документи", "документы",
    "чек", "гарантія", "гарантия", "warranty", "комплект",
    "повний комплект", "полный комплект",
}


@dataclass
class RelevanceResult:
    is_relevant: bool
    reason: str
    confidence: float  # 0.0 – 1.0
    has_accessory_word: bool
    matched_tokens: list[str]
    missing_tokens: list[str]
    urgency_signals: list[str]
    completeness_signals: list[str]


def _tokenize(text: str) -> list[str]:
    """Разбивает строку на значимые токены (слова ≥ 2 символа)."""
    text = text.lower()
    tokens = re.findall(r"[a-zа-яёіїєґ0-9]+", text)
    return [t for t in tokens if len(t) >= 2]


def _normalize(text: str) -> str:
    return text.lower().strip()


def check_relevance(query: str, title: str, description: str = "", price: float = 0.0) -> RelevanceResult:
    """
    Главная функция проверки релевантности.
    
    query   — поисковый запрос пользователя, напр. "iPhone 15 Pro"
    title   — заголовок объявления с OLX
    description — описание объявления
    price   — цена (для sanity check)
    """
    title_norm = _normalize(title)
    desc_norm = _normalize(description)
    full_text = title_norm + " " + desc_norm

    query_tokens = _tokenize(query)

    # ── 1. Проверка слов-паразитов в ЗАГОЛОВКЕ ────────────────────────────────
    title_words = set(_tokenize(title_norm))
    found_accessory = [w for w in ACCESSORY_WORDS if w in title_norm]
    
    if found_accessory:
        return RelevanceResult(
            is_relevant=False,
            reason=f"аксессуар/запчасть: {', '.join(found_accessory[:3])}",
            confidence=0.0,
            has_accessory_word=True,
            matched_tokens=[],
            missing_tokens=query_tokens,
            urgency_signals=[],
            completeness_signals=[],
        )

    # ── 2. Все токены запроса должны быть в заголовке ─────────────────────────
    matched = []
    missing = []
    for token in query_tokens:
        # Точное совпадение или вхождение (напр. "iphone" входит в "iphone15")
        if token in title_norm or any(token in w for w in title_words):
            matched.append(token)
        else:
            missing.append(token)

    # Порог: все токены должны совпасть (строгий режим для точности)
    if missing:
        return RelevanceResult(
            is_relevant=False,
            reason=f"не найдены токены: {', '.join(missing)}",
            confidence=len(matched) / max(len(query_tokens), 1),
            has_accessory_word=False,
            matched_tokens=matched,
            missing_tokens=missing,
            urgency_signals=[],
            completeness_signals=[],
        )

    # ── 3. Собираем сигналы срочности и комплектности ─────────────────────────
    urgency_signals = [w for w in URGENCY_WORDS if w in full_text]
    completeness_signals = [w for w in COMPLETENESS_WORDS if w in full_text]

    confidence = 1.0
    # Небольшой штраф если слова паразиты есть в описании (но не в заголовке)
    desc_accessory = [w for w in ACCESSORY_WORDS if w in desc_norm]
    if desc_accessory:
        confidence = 0.85

    return RelevanceResult(
        is_relevant=True,
        reason="ok",
        confidence=confidence,
        has_accessory_word=False,
        matched_tokens=matched,
        missing_tokens=[],
        urgency_signals=urgency_signals,
        completeness_signals=completeness_signals,
    )


# ─── Sanity check цены ────────────────────────────────────────────────────────

# Минимальные реалистичные цены для популярных категорий (UAH)
PRICE_FLOORS: dict[str, float] = {
    "iphone 15 pro max": 30_000,
    "iphone 15 pro": 25_000,
    "iphone 15": 18_000,
    "iphone 14 pro max": 22_000,
    "iphone 14 pro": 18_000,
    "iphone 14": 14_000,
    "iphone 13": 10_000,
    "iphone 12": 7_000,
    "iphone 11": 5_000,
    "macbook pro": 25_000,
    "macbook air": 20_000,
    "macbook": 15_000,
    "playstation 5": 15_000,
    "ps5": 15_000,
    "playstation 4": 5_000,
    "ps4": 5_000,
    "nintendo switch": 5_000,
    "ipad pro": 15_000,
    "ipad": 6_000,
    "airpods pro": 3_000,
    "airpods": 1_500,
    "apple watch": 5_000,
    "samsung galaxy s24": 20_000,
    "samsung galaxy s23": 15_000,
}


def get_price_floor(query: str) -> float:
    """Возвращает минимальную реалистичную цену для запроса."""
    q = query.lower().strip()
    # Точное совпадение
    if q in PRICE_FLOORS:
        return PRICE_FLOORS[q]
    # Частичное — берём максимальный floor среди совпавших ключей
    floors = [floor for key, floor in PRICE_FLOORS.items() if key in q or q in key]
    return max(floors) if floors else 0.0


def is_price_realistic(price: float, query: str, market_price: float = 0.0) -> tuple[bool, str]:
    """
    Проверяет реалистичность цены.
    Возвращает (True/False, причина).
    """
    if price <= 0:
        return False, "цена не указана"

    floor = get_price_floor(query)
    if floor > 0 and price < floor * 0.15:
        return False, f"цена {price:.0f} грн аномально низкая (мин. ~{floor:.0f} грн)"

    # Если есть рыночная цена — цена не должна быть > 200% от рынка
    if market_price > 0 and price > market_price * 2.0:
        return False, f"цена {price:.0f} грн выше рынка в 2+ раза"

    return True, "ok"
