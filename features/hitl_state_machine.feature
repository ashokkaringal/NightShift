Feature: HITL state machine
  As a property manager
  I want draft status transitions enforced by the database
  So that NightShift never auto-sends outbound messages

  Scenario: staged cannot jump to ready_to_send
  Given a draft in status "staged"
  When manager attempts transition to "ready_to_send"
  Then transition should be rejected

  Scenario: staged to approved is valid
  Given a draft in status "staged"
  When manager approves the draft
  Then status should be "approved"

  Scenario: approved to sent is valid
  Given a draft in status "approved"
  When manager marks draft as sent
  Then status should be "sent"
