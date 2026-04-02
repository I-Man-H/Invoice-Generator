#!/usr/bin/env python3
"""
Invoice Generator
-----------------
Creates a PDF invoice from interactive user input.

Features:
- Company details at the top:
  - Left: company name + logo
  - Right: company contact details
- Customer details section with optional skipping
- Dynamic item table based on number of items entered
- Automatic calculations for:
  - line totals
  - subtotal
  - optional extra discount
  - GST
  - final total
- Outputs a professional PDF invoice

Requirements:
    pip install reportlab

Usage:
    python invoice_generator.py
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path
from typing import List, Dict, Optional
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.utils import ImageReader


TWOPLACES = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def format_money(value: Decimal) -> str:
    return f"${money(value):,.2f}"


def ask_optional(prompt: str) -> str:
    value = input(f"{prompt} (press Enter to skip): ").strip()
    return value


def ask_required(prompt: str) -> str:
    while True:
        value = input(f"{prompt}: ").strip()
        if value:
            return value
        print("This field is required.")


def ask_int(prompt: str, minimum: int = 0) -> int:
    while True:
        raw = input(f"{prompt}: ").strip()
        try:
            value = int(raw)
            if value < minimum:
                print(f"Please enter a number >= {minimum}.")
                continue
            return value
        except ValueError:
            print("Please enter a valid integer.")


def ask_decimal(prompt: str, minimum: Decimal = Decimal("0")) -> Decimal:
    while True:
        raw = input(f"{prompt}: ").strip().replace(",", "")
        try:
            value = Decimal(raw)
            if value < minimum:
                print(f"Please enter a number >= {minimum}.")
                continue
            return money(value)
        except (InvalidOperation, ValueError):
            print("Please enter a valid number.")


def ask_yes_no(prompt: str) -> bool:
    while True:
        raw = input(f"{prompt} [y/n]: ").strip().lower()
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Please type y or n.")


def build_contact_lines(details: Dict[str, str]) -> List[str]:
    lines = []
    for key in ["business_name", "contact_name", "phone", "email", "address", "abn"]:
        value = details.get(key, "").strip()
        if value:
            lines.append(value)
    return lines


def make_paragraphs(lines: List[str], style) -> List[Paragraph]:
    return [Paragraph(line.replace("\n", "<br/>"), style) for line in lines]


def collect_company_details() -> Dict[str, str]:
    print("\n--- Company Details ---")
    print("Enter your company details. Only company name is required.")
    company = {
        "business_name": ask_required("Company name"),
        "contact_name": ask_optional("Contact person / title"),
        "phone": ask_optional("Phone number"),
        "email": ask_optional("Email address"),
        "address": ask_optional("Company address"),
        "abn": ask_optional("ABN"),
        "logo_path": ask_optional("Logo image path (PNG/JPG, optional)"),
    }
    return company


def collect_customer_details() -> Dict[str, str]:
    print("\n--- Customer Details ---")
    print("Enter customer details. You can skip any optional field.")
    customer = {
        "business_name": ask_optional("Customer business name"),
        "contact_name": ask_optional("Customer name"),
        "phone": ask_optional("Customer phone number"),
        "email": ask_optional("Customer email address"),
        "address": ask_optional("Customer address"),
    }
    return customer


def collect_items() -> List[Dict[str, Decimal]]:
    print("\n--- Invoice Items ---")
    count = ask_int("Number of items sold", minimum=1)
    items = []

    for i in range(1, count + 1):
        print(f"\nItem {i}")
        item_name = ask_required("Item description")
        unit = ask_decimal("Quantity / unit", minimum=Decimal("0"))
        unit_price = ask_decimal("Unit price", minimum=Decimal("0"))
        discount = ask_decimal("Item discount amount", minimum=Decimal("0"))

        line_total = money((unit * unit_price) - discount)
        if line_total < 0:
            print("Discount is greater than the line amount. Setting line total to $0.00.")
            line_total = Decimal("0.00")

        items.append(
            {
                "item": item_name,
                "unit": unit,
                "unit_price": money(unit_price),
                "discount": money(discount),
                "total_price": money(line_total),
            }
        )
    return items


def calculate_totals(
    items: List[Dict[str, Decimal]],
    apply_extra_discount: bool,
    extra_discount: Decimal,
    gst_rate_percent: Decimal,
) -> Dict[str, Decimal]:
    subtotal = money(sum(item["total_price"] for item in items))

    adjusted_subtotal = subtotal
    if apply_extra_discount:
        adjusted_subtotal = money(subtotal - extra_discount)
        if adjusted_subtotal < 0:
            adjusted_subtotal = Decimal("0.00")

    gst = money(adjusted_subtotal * gst_rate_percent / Decimal("100"))
    total_amount = money(adjusted_subtotal + gst)

    return {
        "subtotal": subtotal,
        "extra_discount": money(extra_discount if apply_extra_discount else Decimal("0")),
        "adjusted_subtotal": adjusted_subtotal,
        "gst": gst,
        "total_amount": total_amount,
    }


def create_invoice_pdf(
    filename: str,
    company: Dict[str, str],
    customer: Dict[str, str],
    items: List[Dict[str, Decimal]],
    totals: Dict[str, Decimal],
    invoice_number: str,
    invoice_date: str,
    gst_rate_percent: Decimal,
):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="RightSmall",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_RIGHT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="LeftSmall",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading3"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1F3A5F"),
            spaceAfter=4,
        )
    )

    story = []

    # Header left: company name + logo
    left_parts = []
    logo_path = company.get("logo_path", "").strip()

    if logo_path:
        path = Path(logo_path)
        if path.exists():
            try:
                image_reader = ImageReader(str(path))
                img_width, img_height = image_reader.getSize()
                max_width = 45 * mm
                scale = min(1, max_width / img_width)
                left_parts.append(
                    Image(
                        str(path),
                        width=img_width * scale,
                        height=img_height * scale,
                    )
                )
                left_parts.append(Spacer(1, 4))
            except Exception:
                pass

    left_parts.append(Paragraph(f"<b>{company['business_name']}</b>", styles["Title"]))

    company_lines = build_contact_lines(company)
    if company_lines:
        company_para = Paragraph("<br/>".join(company_lines), styles["RightSmall"])
    else:
        company_para = Paragraph("", styles["RightSmall"])

    header_table = Table(
        [[left_parts, company_para]],
        colWidths=[95 * mm, 75 * mm],
        hAlign="LEFT",
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.append(header_table)
    story.append(Spacer(1, 8))

    title_table = Table(
        [[Paragraph("<b>INVOICE</b>", styles["Heading1"]),
          Paragraph(f"<b>Invoice #:</b> {invoice_number}<br/><b>Date:</b> {invoice_date}", styles["RightSmall"])]],
        colWidths=[95 * mm, 75 * mm],
    )
    title_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(title_table)
    story.append(Spacer(1, 8))

    # Customer details
    story.append(Paragraph("Bill To", styles["SectionHeader"]))
    customer_lines = []
    for key in ["business_name", "contact_name", "address", "phone", "email"]:
        value = customer.get(key, "").strip()
        if value:
            customer_lines.append(value)

    if not customer_lines:
        customer_lines = ["No customer details provided"]

    customer_table = Table(
        [[Paragraph("<br/>".join(customer_lines), styles["LeftSmall"])]],
        colWidths=[170 * mm],
    )
    customer_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, colors.grey),
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(customer_table)
    story.append(Spacer(1, 10))

    # Items table
    table_data = [
        [
            "Items",
            "Unit",
            "Unit Price",
            "Discount",
            "Total Price",
        ]
    ]

    for item in items:
        table_data.append(
            [
                item["item"],
                f"{item['unit']}",
                format_money(item["unit_price"]),
                format_money(item["discount"]),
                format_money(item["total_price"]),
            ]
        )

    summary_rows = [
        ["", "", "", "Subtotal", format_money(totals["subtotal"])],
    ]

    if totals["extra_discount"] > 0:
        summary_rows.append(["", "", "", "Extra Discount", f"-{format_money(totals['extra_discount'])}"])
        summary_rows.append(["", "", "", "After Discount", format_money(totals["adjusted_subtotal"])])

    summary_rows.append(["", "", "", f"GST ({gst_rate_percent}%)", format_money(totals["gst"])])
    summary_rows.append(["", "", "", "Total Amount", format_money(totals["total_amount"])])

    table_data.extend(summary_rows)

    item_table = Table(
        table_data,
        colWidths=[66 * mm, 20 * mm, 28 * mm, 24 * mm, 32 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )

    last_row = len(table_data) - 1
    item_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("SPAN", (0, len(items) + 1), (2, len(items) + 1)),
            ]
        )
    )

    # Style summary rows
    summary_start = len(items) + 1
    for row in range(summary_start, len(table_data)):
        item_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (3, row), (4, row), colors.whitesmoke),
                    ("FONTNAME", (3, row), (4, row), "Helvetica-Bold" if row == last_row else "Helvetica"),
                ]
            )
        )

    story.append(item_table)
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "Thank you for your business.",
            styles["Italic"],
        )
    )

    doc.build(story)


def main():
    print("PDF Invoice Generator")
    print("=====================")

    company = collect_company_details()
    customer = collect_customer_details()
    items = collect_items()

    print("\n--- Invoice Settings ---")
    invoice_number = ask_optional("Invoice number")
    if not invoice_number:
        invoice_number = "INV-001"

    invoice_date = ask_optional("Invoice date (e.g. 01/04/2026)")
    if not invoice_date:
        invoice_date = "01/04/2026"

    gst_rate = ask_decimal("GST rate percentage (normally 10)", minimum=Decimal("0"))

    apply_extra_discount = ask_yes_no("Apply an additional invoice-level discount")
    extra_discount = Decimal("0.00")
    if apply_extra_discount:
        extra_discount = ask_decimal("Enter extra discount amount", minimum=Decimal("0"))

    output_name = ask_optional("Output PDF filename")
    if not output_name:
        output_name = "invoice.pdf"

    if not output_name.lower().endswith(".pdf"):
        output_name += ".pdf"

    totals = calculate_totals(
        items=items,
        apply_extra_discount=apply_extra_discount,
        extra_discount=extra_discount,
        gst_rate_percent=gst_rate,
    )

    create_invoice_pdf(
        filename=output_name,
        company=company,
        customer=customer,
        items=items,
        totals=totals,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        gst_rate_percent=gst_rate,
    )

    print("\nInvoice created successfully:")
    print(Path(output_name).resolve())
    print("\nSummary:")
    print(f"Subtotal:      {format_money(totals['subtotal'])}")
    if totals["extra_discount"] > 0:
        print(f"Extra Discount:{format_money(totals['extra_discount'])}")
        print(f"After Discount:{format_money(totals['adjusted_subtotal'])}")
    print(f"GST:           {format_money(totals['gst'])}")
    print(f"Total Amount:  {format_money(totals['total_amount'])}")


if __name__ == "__main__":
    main()
