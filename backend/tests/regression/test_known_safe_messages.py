"""
Regression test: known-safe messages must not trigger high risk levels.

These are ordinary personal/transactional texts (bills, deliveries, OTPs,
casual plans, salary/payment confirmations, college/work admin) that the
pipeline should classify as VERY LOW or LOW risk.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from services.orchestrator import analyze_text


# Messages from the original task specification
ORIGINAL_SAFE_MESSAGES = [
    "Hey, are we still meeting for lunch tomorrow at 1pm?",
    "Mom, I landed safely. Will call you once I reach the hotel.",
    "Reminder: your dentist appointment is on Friday at 10am.",
    "Can you send me the notes from todays class?",
    "Happy birthday! Hope you have an amazing day.",
    "Your Amazon order 402-1194 has been shipped and will arrive Tuesday.",
    "Team meeting moved to 3pm today, conference room B.",
    "Thanks for helping me move last weekend, really appreciate it.",
    "Electricity bill for this month is Rs. 1240, due on the 15th.",
    "Can you pick up milk on your way home?",
    "Your OTP for login is 482913, valid for 10 minutes.",
    "Congrats on the new job! When do you start?",
    "The train to Chennai is delayed by 20 minutes.",
    "Please review the attached PDF before our call tomorrow.",
    "Your package from Flipkart was delivered today at 2:15pm.",
    "Dinner at my place Saturday, 7pm, bring nothing just yourself.",
    "Your bank statement for August is now available in net banking.",
    "Class is cancelled tomorrow due to the holiday.",
    "Good morning! Dont forget the meeting with the professor at 11.",
    "Can you transfer me 500 rupees for the movie tickets, Ill pay you back tomorrow.",
]

# Additional safe messages written for this test (Indian-context personal/transactional)
EXTRA_SAFE_MESSAGES = [
    "Salary credited to your account ending 4521. Net pay: Rs. 42,350.",
    "Your SBI account balance is Rs. 15,230 as of 28 Aug.",
    "UPI payment of Rs. 350 to Swiggy on 27 Aug successful. Ref: 512345678901.",
    "Your Airtel bill of Rs. 799 is due on 5 Sep. Pay via app or website.",
    "Office holiday tomorrow. Enjoy the long weekend!",
    "Meeting with client rescheduled to Thursday 4pm. Please update your calendar.",
    "Water bill for August: Rs. 520. Last date to pay without late fee: 10 Sep.",
    "Your IRCTC ticket 2245678901 is confirmed. Train: Chennai Express, Dep: 6:30am.",
    "Lunch is ready. Come home by 1pm if you can.",
    "College fest tickets are Rs. 200 for students. Get them from the admin office.",
    "Your courier from Blue Dart has been dispatched. Tracking: BD123456789.",
    "Wi-Fi password for the guest network is Welcome2026.",
    "Monthly metro pass costs Rs. 1000. Valid from 1st to 30th Sep.",
    "Team outing this Friday. Meeting at office parking lot at 9am sharp.",
    "Doctor appointment confirmed for 3 Sep at 11:30am. Dr. Sharma, Room 4.",
]

ALL_SAFE_MESSAGES = ORIGINAL_SAFE_MESSAGES + EXTRA_SAFE_MESSAGES


@pytest.mark.parametrize("message", ALL_SAFE_MESSAGES, ids=[f"safe_{i}" for i in range(len(ALL_SAFE_MESSAGES))])
def test_message_classified_as_low_risk(message: str) -> None:
    """Every known-safe message must produce a VERY LOW or LOW risk level."""
    result = analyze_text(message)
    risk_level = result.get("risk_level", "UNKNOWN")
    assert risk_level in ("VERY LOW", "LOW"), (
        f"Expected VERY LOW or LOW for safe message, got {risk_level!r}.\n"
        f"Message: {message!r}\n"
        f"Full result keys: {list(result.keys())}"
    )


def test_all_safe_messages_pass() -> None:
    """Batch check: count how many of the 35 safe messages pass."""
    passed = 0
    failed = []
    for msg in ALL_SAFE_MESSAGES:
        result = analyze_text(msg)
        rl = result.get("risk_level", "UNKNOWN")
        if rl in ("VERY LOW", "LOW"):
            passed += 1
        else:
            failed.append((msg, rl))
    total = len(ALL_SAFE_MESSAGES)
    assert passed == total, (
        f"{passed}/{total} safe messages passed. Failures:\n"
        + "\n".join(f"  {msg!r} -> {rl}" for msg, rl in failed)
    )
