from datetime import date

from app.ingest.source import hidden_fields, iter_months, parse_announcements, parse_date

LISTING = b"""
<html><body>
<form>
  <input type="hidden" name="__VIEWSTATE" value="abc" />
  <input type="hidden" name="hdnYear" value="" />
  <input type="hidden" name="hdnMonth" value="0" />
  <input type="hidden" name="__EVENTVALIDATION" value="xyz" />
</form>
<table class="tablebg">
  <tr><td class="tableheader" colspan="4"><b>Mar 28, 2025</b></td></tr>
  <tr>
    <td><a class='link2' href=NotificationUser.aspx?Id=13748&Mode=0 >Special Clearing Operations</a></td>
    <td colspan="3"><a href="https://rbidocs.rbi.org.in/rdocs/notification/PDFs/A.PDF">PDF</a></td>
  </tr>
  <tr><td class="tableheader"><b>Mar 24, 2025</b></td></tr>
  <tr>
    <td><a class='link2' href=NotificationUser.aspx?Id=13726&Mode=0 >Priority Sector Lending</a></td>
    <td><a href="https://rbidocs.rbi.org.in/rdocs/notification/PDFs/B.PDF">PDF</a></td>
  </tr>
</table>
</body></html>
"""


def test_parses_rows_with_dates_and_pdfs():
    items = parse_announcements(LISTING)
    assert len(items) == 2
    assert items[0].title == "Special Clearing Operations"
    assert items[0].date_issued == date(2025, 3, 28)
    assert items[0].pdf_url == "https://rbidocs.rbi.org.in/rdocs/notification/PDFs/A.PDF"
    assert items[0].detail_url == "https://www.rbi.org.in/scripts/NotificationUser.aspx?Id=13748&Mode=0"
    assert items[1].date_issued == date(2025, 3, 24)


def test_hidden_fields_are_collected():
    fields = hidden_fields(LISTING)
    assert fields["__VIEWSTATE"] == "abc"
    assert fields["hdnMonth"] == "0"
    assert "__EVENTVALIDATION" in fields


def test_parse_date_accepts_short_and_long_months():
    assert parse_date("Mar 28, 2025") == date(2025, 3, 28)
    assert parse_date("March 28, 2025") == date(2025, 3, 28)
    assert parse_date("not a date") is None


def test_iter_months_crosses_year_boundary():
    months = list(iter_months((2024, 11), (2025, 2)))
    assert months == [(2024, 11), (2024, 12), (2025, 1), (2025, 2)]
