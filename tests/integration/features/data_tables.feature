Feature: behave-data MVP integration
  Scenario: Typed table conversion
    Given a table with typed columns
      | name:str | age:int | active:bool |
      | Alice    | 30      | true        |
      | Bob      | 25      | false       |
    Then the typed dicts should have correct types

  Scenario: Null resolution in table
    Given a table with null markers
      | name:str | age:int? |
      | Alice    | 30       |
      | null     | N/A      |
    Then null cells should be resolved to None

  Scenario: Raw table access
    Given a table without assuming header
      | col1 | col2 |
      | a    | b    |
      | c    | d    |
    Then the raw table should have 3 rows total

  Scenario: Table diff
    Given an expected table
      | name |
      | Alice |
    When the actual table differs
      | name |
      | Bob |
    Then the diff should raise an error
