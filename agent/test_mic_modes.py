#!/usr/bin/env python3
"""
Quick test to verify AI mode logic works correctly
"""

def test_ai_mode_logic():
    """Test that AI mode correctly filters students vs teachers"""

    # Simulate participant identities
    test_cases = [
        ("Student-abc123", True, "Should allow student"),
        ("Student-xyz789", True, "Should allow student"),
        ("Teacher", False, "Should reject teacher"),
        ("teacher-john", False, "Should reject teacher (lowercase)"),
        ("TEACHER-JANE", False, "Should reject teacher (uppercase)"),
    ]

    ai_mode_participants = set()

    for identity, should_allow, description in test_cases:
        # Check if teacher (backend logic)
        is_teacher = "teacher" in identity.lower()

        if is_teacher:
            print(f"❌ REJECTED: {identity} - {description}")
            assert not should_allow, f"Failed: {description}"
        else:
            ai_mode_participants.add(identity)
            print(f"✅ ALLOWED: {identity} - {description}")
            assert should_allow, f"Failed: {description}"

    print(f"\n✅ All tests passed!")
    print(f"AI mode participants: {ai_mode_participants}")

if __name__ == "__main__":
    test_ai_mode_logic()
