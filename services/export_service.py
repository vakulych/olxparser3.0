import csv
import json
import io
from openpyxl import Workbook
from database.models.ad_sent import AdSent


def export_to_csv(ads: list[AdSent]) -> bytes:
    """Экспорт в CSV (только товары пользователя)."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Название", "Цена", "Рынок", "Прибыль", "ROI", "Flip Score",
        "Город", "Продавец", "Статус продавца", "Ключевое слово", "Ссылка", "Дата"
    ])
    for ad in ads:
        writer.writerow([
            ad.olx_id, ad.title, ad.price, ad.market_price, ad.profit,
            ad.roi, ad.flip_score, ad.city, ad.seller_name, ad.seller_status,
            ad.keyword, ad.url, ad.created_at.strftime("%Y-%m-%d %H:%M")
        ])
    return output.getvalue().encode("utf-8-sig")


def export_to_excel(ads: list[AdSent]) -> bytes:
    """Экспорт в Excel (только товары пользователя)."""
    wb = Workbook()
    ws = wb.active
    ws.title = "OLX Deals"
    headers = [
        "ID", "Название", "Цена", "Рынок", "Прибыль", "ROI", "Flip Score",
        "Город", "Продавец", "Статус", "Ключевое слово", "Ссылка", "Дата"
    ]
    ws.append(headers)
    for ad in ads:
        ws.append([
            ad.olx_id, ad.title, ad.price, ad.market_price, ad.profit,
            ad.roi, ad.flip_score, ad.city, ad.seller_name, ad.seller_status,
            ad.keyword, ad.url, ad.created_at.strftime("%Y-%m-%d %H:%M")
        ])
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def export_to_json(ads: list[AdSent]) -> bytes:
    """Экспорт в JSON (только товары пользователя)."""
    data = [
        {
            "id": ad.olx_id, "title": ad.title, "price": ad.price,
            "market_price": ad.market_price, "profit": ad.profit,
            "roi": ad.roi, "flip_score": ad.flip_score,
            "city": ad.city, "seller": ad.seller_name,
            "seller_status": ad.seller_status, "keyword": ad.keyword,
            "url": ad.url, "date": ad.created_at.isoformat()
        }
        for ad in ads
    ]
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
