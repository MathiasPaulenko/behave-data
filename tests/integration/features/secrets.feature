Feature: Secrets and placeholder resolution E2E

  Scenario: Resolve env placeholder in step
    Given I set environment variable "TEST_SECRET" to "my_secret_value"
    When I resolve the placeholder "env:TEST_SECRET"
    Then the resolved value should be "my_secret_value"

  Scenario: Resolve plain text passthrough
    When I resolve the placeholder "just_plain_text"
    Then the resolved value should be "just_plain_text"

  Scenario: Mask a resolved env value
    Given I set environment variable "API_TOKEN" to "secret_token_123"
    When I resolve and mask the placeholder "env:API_TOKEN"
    Then the masked value should be "secret_token_123"

  Scenario: Resolve integer passthrough
    When I resolve the value 42
    Then the resolved value should be "42"
