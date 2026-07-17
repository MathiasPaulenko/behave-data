Feature: Nullable types in tables
  Scenario: Nullable int column with empty cell
    Given a table with nullable columns
      | name:str | doors:int? |
      | Alice    | 3          |
      | Bob      |            |
    Then null cells should be resolved to None
