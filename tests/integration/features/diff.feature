Feature: Table diff comparison
  Scenario: Different tables should raise diff error
    Given an expected table
      | name |
      | Alice |
    When the actual table differs
      | name |
      | Bob |
    Then the diff should raise an error

  Scenario: Identical tables should not raise
    Given an expected table
      | name |
      | Alice |
    When the actual table is the same
      | name |
      | Alice |
    Then the diff should not raise an error
