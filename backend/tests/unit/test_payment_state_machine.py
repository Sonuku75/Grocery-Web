"""
Unit tests for Payment State Machine (Module 12)
"""

import pytest
from app.core.errors import ValidationError
from app.models.payment import PaymentStatus
from app.services.payment_service import PaymentStateMachine


def test_payment_state_machine_valid_transitions():
    """Verify all legal lifecycle transitions."""
    # From PENDING
    PaymentStateMachine.validate_transition(PaymentStatus.PENDING.value, PaymentStatus.AUTHORIZED.value)
    PaymentStateMachine.validate_transition(PaymentStatus.PENDING.value, PaymentStatus.PAID.value)
    PaymentStateMachine.validate_transition(PaymentStatus.PENDING.value, PaymentStatus.FAILED.value)
    PaymentStateMachine.validate_transition(PaymentStatus.PENDING.value, PaymentStatus.CANCELLED.value)

    # From AUTHORIZED
    PaymentStateMachine.validate_transition(PaymentStatus.AUTHORIZED.value, PaymentStatus.PAID.value)
    PaymentStateMachine.validate_transition(PaymentStatus.AUTHORIZED.value, PaymentStatus.FAILED.value)
    PaymentStateMachine.validate_transition(PaymentStatus.AUTHORIZED.value, PaymentStatus.CANCELLED.value)

    # From PAID
    PaymentStateMachine.validate_transition(PaymentStatus.PAID.value, PaymentStatus.REFUND_PENDING.value)
    PaymentStateMachine.validate_transition(PaymentStatus.PAID.value, PaymentStatus.PARTIALLY_REFUNDED.value)
    PaymentStateMachine.validate_transition(PaymentStatus.PAID.value, PaymentStatus.REFUNDED.value)

    # From REFUND_PENDING
    PaymentStateMachine.validate_transition(PaymentStatus.REFUND_PENDING.value, PaymentStatus.PARTIALLY_REFUNDED.value)
    PaymentStateMachine.validate_transition(PaymentStatus.REFUND_PENDING.value, PaymentStatus.REFUNDED.value)
    PaymentStateMachine.validate_transition(PaymentStatus.REFUND_PENDING.value, PaymentStatus.PAID.value)

    # From PARTIALLY_REFUNDED
    PaymentStateMachine.validate_transition(PaymentStatus.PARTIALLY_REFUNDED.value, PaymentStatus.REFUND_PENDING.value)
    PaymentStateMachine.validate_transition(PaymentStatus.PARTIALLY_REFUNDED.value, PaymentStatus.PARTIALLY_REFUNDED.value)
    PaymentStateMachine.validate_transition(PaymentStatus.PARTIALLY_REFUNDED.value, PaymentStatus.REFUNDED.value)

    # Same state is a no-op and always valid
    PaymentStateMachine.validate_transition(PaymentStatus.PENDING.value, PaymentStatus.PENDING.value)
    PaymentStateMachine.validate_transition(PaymentStatus.PAID.value, PaymentStatus.PAID.value)


def test_payment_state_machine_terminal_states_cannot_transition():
    """Verify terminal states (FAILED, CANCELLED, REFUNDED) reject transitions."""
    with pytest.raises(ValidationError):
        PaymentStateMachine.validate_transition(PaymentStatus.FAILED.value, PaymentStatus.PAID.value)

    with pytest.raises(ValidationError):
        PaymentStateMachine.validate_transition(PaymentStatus.CANCELLED.value, PaymentStatus.PAID.value)

    with pytest.raises(ValidationError):
        PaymentStateMachine.validate_transition(PaymentStatus.REFUNDED.value, PaymentStatus.PAID.value)

    with pytest.raises(ValidationError):
        PaymentStateMachine.validate_transition(PaymentStatus.REFUNDED.value, PaymentStatus.PENDING.value)


def test_payment_state_machine_illegal_jumps():
    """Verify illegal jumps are strictly blocked."""
    # Cannot jump from PENDING straight to REFUNDED without being PAID
    with pytest.raises(ValidationError):
        PaymentStateMachine.validate_transition(PaymentStatus.PENDING.value, PaymentStatus.REFUNDED.value)

    with pytest.raises(ValidationError):
        PaymentStateMachine.validate_transition(PaymentStatus.PENDING.value, PaymentStatus.PARTIALLY_REFUNDED.value)

    # Cannot jump from PAID back to PENDING
    with pytest.raises(ValidationError):
        PaymentStateMachine.validate_transition(PaymentStatus.PAID.value, PaymentStatus.PENDING.value)
