from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT_DIR = Path("data/demo/policies")

POLICIES = {
    "priority_sector_lending_policy.pdf": [
        ("h", "1. Purpose"),
        ("p", "This policy sets out how the Company meets its priority sector lending obligations under Reserve Bank of India directions."),
        ("h", "2. Targets"),
        ("p", "2.1 The Company shall ensure that priority sector lending is not less than forty per cent of adjusted net bank credit at the end of every financial year."),
        ("p", "2.2 The Company shall achieve a sub-target of ten per cent of adjusted net bank credit for small and marginal farmers."),
        ("p", "2.3 The Company shall achieve a sub-target of seven and a half per cent of adjusted net bank credit for micro enterprises."),
        ("h", "3. Eligible Categories"),
        ("p", "3.1 The Company shall classify loans to agriculture, micro enterprises, education, housing and renewable energy as eligible priority sector loans."),
        ("h", "4. Reporting"),
        ("p", "4.1 The Compliance Officer shall report the outstanding priority sector position to the Board every quarter."),
        ("p", "4.2 The Company shall submit the quarterly priority sector return to the Reserve Bank of India within the prescribed timeline."),
        ("h", "5. Shortfall"),
        ("p", "5.1 Where the Company falls short of the target, it may purchase Priority Sector Lending Certificates to meet the shortfall."),
        ("h", "6. Records"),
        ("p", "6.1 The Company shall maintain disaggregated data of priority sector loans by category and sub-category."),
        ("h", "7. Review"),
        ("p", "7.1 This policy shall be reviewed annually by the Board."),
    ],
    "kyc_policy.pdf": [
        ("h", "1. Customer Due Diligence"),
        ("p", "1.1 We verify the identity of every customer before opening an account, using PAN and Aadhaar based verification."),
        ("p", "1.2 Enhanced due diligence is applied to politically exposed persons and to customers in high risk categories."),
        ("h", "2. Record Keeping"),
        ("p", "2.1 Records of customer transactions and identity documents are retained for five years after the relationship ends."),
        ("h", "3. Periodic Updation"),
        ("p", "3.1 High risk customers are reviewed annually and low risk customers every ten years."),
    ],
    "grievance_policy.pdf": [
        ("h", "1. Complaint Handling"),
        ("p", "1.1 Every complaint is acknowledged within forty eight hours and resolved within thirty days of receipt."),
        ("h", "2. Nodal Officer"),
        ("p", "2.1 A nodal officer is appointed to oversee complaint resolution and to report to the board every quarter."),
    ],
    "outsourcing_policy.pdf": [
        ("h", "1. Vendor Due Diligence"),
        ("p", "1.1 We conduct due diligence on every service provider before onboarding and review it every two years."),
        ("h", "2. Customer Data"),
        ("p", "2.1 Customer data shared with vendors is limited to what is required for the service, and the vendor must not use it for any other purpose."),
    ],
}


def build() -> list[Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for name, blocks in POLICIES.items():
        path = OUT_DIR / name
        pdf = canvas.Canvas(str(path), pagesize=A4)
        y = A4[1] - 80
        for kind, text in blocks:
            if kind == "h":
                y -= 26
                pdf.setFont("Helvetica-Bold", 13)
            else:
                y -= 16
                pdf.setFont("Helvetica", 10)
            pdf.drawString(72, y, text)
            if y < 100:
                pdf.showPage()
                y = A4[1] - 80
        pdf.save()
        written.append(path)
    return written


if __name__ == "__main__":
    for path in build():
        print(path)
