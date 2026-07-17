Feature: Raw table access without header assumption
  Scenario: Access all rows including header
    Given a table without assuming header
      | col1 | col2 |
      | a    | b    |
      | c    | d    |
    Then the raw table should have 3 rows total
