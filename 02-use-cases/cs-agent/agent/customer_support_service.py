from __future__ import annotations

from datetime import datetime
import re

from .customer_support_repository import LocalCustomerSupportRepository


class CustomerSupportService:
    def __init__(self, repository: LocalCustomerSupportRepository):
        self.repository = repository

    def get_customer_profile(
        self,
        customer_id: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> str:
        if not any([customer_id, email, phone]):
            raise ValueError(
                "Must provide at least one search parameter: customer_id, email, or phone"
            )
        if email and not validate_email(email):
            raise ValueError("Invalid email format")
        if phone and not validate_phone(phone):
            raise ValueError("Invalid phone number format")

        customer = self.repository.find_customer(
            customer_id=customer_id,
            email=email,
            phone=phone,
        )
        search_value = customer_id or email or phone

        if not customer:
            return "\n".join(
                [
                    "❌ Customer Profile Not Found",
                    "=============================",
                    f"🔍 Search Value: {search_value}",
                    "",
                    "This customer was not found in the local support dataset.",
                    "Please verify the information and try again.",
                ]
            )

        customer_id_value = customer.get("customer_id", "Unknown")
        first_name = customer.get("first_name", "Unknown")
        last_name = customer.get("last_name", "Unknown")
        email_value = customer.get("email", "Not provided")
        phone_value = customer.get("phone", "Not provided")
        address = format_address(customer.get("address", {}))
        registration_date = customer.get("registration_date", "Unknown")
        tier = customer.get("tier", "Standard")
        support_cases = customer.get("support_cases_count", 0)
        total_purchases = customer.get("total_purchases", 0)
        lifetime_value = customer.get("lifetime_value", 0.0)
        notes = customer.get("notes", "No notes on file")
        preferences = format_preferences(customer.get("communication_preferences", {}))
        tenure = format_tenure(registration_date)

        profile_info = [
            "👤 Customer Profile Information",
            "===============================",
            f"🆔 Customer ID: {customer_id_value}",
            f"📛 Name: {first_name} {last_name}",
            f"📧 Email: {email_value}",
            f"📱 Phone: {phone_value}",
            f"🏠 Address: {address}",
            f"🏅 Tier: {tier}",
            f"🗓️ Registered: {registration_date} ({tenure})",
            f"📨 Communication Preferences: {preferences}",
            f"🎫 Support Cases: {support_cases}",
            f"🛒 Total Purchases: {total_purchases}",
            f"💰 Lifetime Value: ${lifetime_value:,.2f}",
            f"📝 Notes: {notes}",
        ]
        return "\n".join(profile_info)

    def check_warranty_status(
        self, serial_number: str, customer_email: str | None = None
    ) -> str:
        if not validate_serial_number(serial_number):
            raise ValueError("Serial number must be 8-20 alphanumeric characters")

        warranty = self.repository.find_warranty(serial_number)
        serial_number = serial_number.upper()
        if not warranty:
            return "\n".join(
                [
                    "❌ Warranty Not Found",
                    "====================",
                    f"🔍 Serial Number: {serial_number}",
                    "",
                    "This serial number was not found in the local warranty dataset.",
                    "Please verify the serial number and try again.",
                ]
            )

        customer = self.repository.find_customer(customer_id=warranty.get("customer_id"))
        if customer_email and customer and customer.get("email", "").lower() != customer_email.lower():
            return "\n".join(
                [
                    "❌ Warranty Verification Failed",
                    "==============================",
                    f"🔍 Serial Number: {serial_number}",
                    f"📧 Provided Email: {customer_email}",
                    "",
                    "The provided email does not match the customer associated with this warranty record.",
                ]
            )

        warranty_end_date = warranty.get("warranty_end_date", "Unknown")
        days_remaining = calculate_days_remaining(warranty_end_date)
        status_text = get_warranty_status_text(days_remaining)
        customer_name = (
            f"{customer.get('first_name', 'Unknown')} {customer.get('last_name', '')}".strip()
            if customer
            else "Unknown"
        )

        warranty_info = [
            "🛡️ Warranty Status Information",
            "===============================",
            f"📱 Product: {warranty.get('product_name', 'Unknown Product')}",
            f"🔢 Serial Number: {serial_number}",
            f"👤 Customer: {customer_name}",
            f"📅 Purchase Date: {warranty.get('purchase_date', 'Unknown')}",
            f"⏰ Warranty End Date: {warranty_end_date}",
            f"📋 Warranty Type: {warranty.get('warranty_type', 'Standard')}",
            f"🔍 Status: {status_text}",
            "",
        ]

        if days_remaining > 0:
            warranty_info.append(f"📆 Days Remaining: {days_remaining} days")
        elif days_remaining == 0:
            warranty_info.append("📆 Warranty expires today!")
        else:
            warranty_info.append(f"📆 Expired {abs(days_remaining)} days ago")

        warranty_info.extend(
            [
                "",
                "🔧 Coverage Details:",
                f"   {warranty.get('coverage_details', 'Standard coverage applies')}",
                f"🏬 Store Location: {warranty.get('store_location', 'Unknown')}",
                f"💵 Purchase Price: ${warranty.get('purchase_price', 0):,.2f}",
            ]
        )
        return "\n".join(warranty_info)


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    cleaned_phone = re.sub(r"[^\d]", "", phone)
    return 10 <= len(cleaned_phone) <= 15


def validate_serial_number(serial_number: str) -> bool:
    return bool(re.match(r"^[A-Z0-9]{8,20}$", serial_number.upper()))


def calculate_days_remaining(end_date: str) -> int:
    try:
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        return (end_date_obj - datetime.now()).days
    except ValueError:
        return 0


def get_warranty_status_text(days_remaining: int) -> str:
    if days_remaining > 30:
        return "✅ Active"
    if days_remaining > 0:
        return "⚠️ Expiring Soon"
    return "❌ Expired"


def format_address(address: dict) -> str:
    parts = [
        address.get("street"),
        address.get("city"),
        address.get("state"),
        address.get("zip_code"),
        address.get("country"),
    ]
    return ", ".join(part for part in parts if part) or "No address on file"


def format_preferences(preferences: dict) -> str:
    enabled = []
    if preferences.get("email"):
        enabled.append("Email")
    if preferences.get("sms"):
        enabled.append("SMS")
    if preferences.get("phone"):
        enabled.append("Phone")
    return ", ".join(enabled) if enabled else "No communication preferences set"


def format_tenure(registration_date: str) -> str:
    try:
        reg_date = datetime.strptime(registration_date, "%Y-%m-%d")
        tenure_days = (datetime.now() - reg_date).days
        years = tenure_days // 365
        months = (tenure_days % 365) // 30
        if years:
            return f"{years}y {months}m customer"
        return f"{months}m customer"
    except ValueError:
        return "tenure unavailable"
