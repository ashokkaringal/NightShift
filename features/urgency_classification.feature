Feature: Urgency classification
  As a property manager
  I want overnight items classified by urgency
  So that RED items surface first in the morning brief

  Scenario: Water stain hard case is RED
    Given an inbox item with id "email-001"
    When TriageAgent classifies the item
    Then urgency tier should be "RED"

  Scenario: Routine lightbulb request is GREEN
    Given an inbox item with id "email-002"
    When TriageAgent classifies the item
    Then urgency tier should be "GREEN"

  Scenario: No heat in winter is RED
    Given an inbox item with id "email-003"
    When TriageAgent classifies the item
    Then urgency tier should be "RED"
