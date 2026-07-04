Feature: HITL state machine
  As a property manager
  I want draft status transitions enforced by the database
  So that NightShift never auto-sends outbound messages

  Scenario: staged cannot jump to ready_to_send
    Given a draft in status "staged"
    When manager attempts transition to "ready_to_send"
    Then transition should be rejected

  Scenario: staged to approved is valid with manager identity
    Given a draft in status "staged"
    When manager approves with name "Jane Doe"
    Then status should be "approved"

  Scenario: rejected drafts cannot transition
    Given a draft in status "rejected"
    When manager attempts transition to "approved"
    Then transition should be rejected
