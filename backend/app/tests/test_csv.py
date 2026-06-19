import pytest

from app.db.models import CsvUpload
from app.services.csv_service import parse_and_aggregate_csv


class StubUpload:
    def __init__(self, filename: str, content: str):
        self.filename = filename
        self._content = content.encode("utf-8")

    async def read(self) -> bytes:
        return self._content


def _upload(name: str, content: str) -> StubUpload:
    return StubUpload(name, content)


@pytest.mark.asyncio
async def test_parse_and_aggregate_csv_categorises_and_persists(db_session, make_user):
    user = make_user()
    upload = _upload(
        "bank.csv",
        "\n".join(
            [
                "Date,Description,Amount",
                "2026-03-01,Tesco,-45.20",
                "2026-03-02,Uber,-12.50",
                "2026-03-03,Netflix,-9.99",
                "2026-03-04,Unknown Shop,-5.00",
            ]
        ),
    )

    result = await parse_and_aggregate_csv(db_session, user=user, upload=upload, save_audit=True)

    assert result["parsed_count"] == 4
    assert result["warnings"] == []
    assert result["category_totals"]["groceries"] == 45.2
    assert result["category_totals"]["transport"] == 12.5
    assert result["category_totals"]["subscriptions"] == 9.99
    assert result["category_totals"]["other"] == 5.0
    assert result["transactions"][0]["suggested_category"] == "groceries"
    assert result["transactions"][0]["method"] == "merchant_map"
    assert result["transactions"][2]["suggested_category"] == "subscriptions"
    assert result["transactions"][2]["confidence"] >= 0.9

    rows = db_session.query(CsvUpload).filter(CsvUpload.user_id == user.id).all()
    assert len(rows) == 1
    assert rows[0].filename == "bank.csv"
    assert rows[0].category_totals["groceries"] == 45.2


@pytest.mark.asyncio
async def test_parse_and_aggregate_csv_reports_missing_header(db_session, make_user):
    user = make_user()
    upload = _upload("empty.csv", "")

    result = await parse_and_aggregate_csv(db_session, user=user, upload=upload, save_audit=False)

    assert result["parsed_count"] == 0
    assert result["transactions"] == []
    assert result["category_totals"] == {}
    assert result["warnings"] == ["CSV has no header row"]


@pytest.mark.asyncio
async def test_parse_and_aggregate_csv_warns_on_bad_amount(db_session, make_user):
    user = make_user()
    upload = _upload(
        "bad.csv",
        "\n".join(
            [
                "Date,Description,Amount",
                "2026-03-01,Tesco,not-a-number",
            ]
        ),
    )

    result = await parse_and_aggregate_csv(db_session, user=user, upload=upload, save_audit=False)

    assert result["parsed_count"] == 1
    assert result["category_totals"]["groceries"] == 0.0
    assert "failed to parse amount" in result["warnings"][0]
