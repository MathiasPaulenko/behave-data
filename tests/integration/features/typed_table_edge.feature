Feature: Typed table edge cases E2E

  Scenario: All supported types in one table
    Given a table with all types
      | name:str | age:int | price:float | active:bool | created:date |
      | Alice    | 30      | 99.99       | true        | 2024-01-15   |
      | Bob      | 25      | 49.50       | false       | 2024-06-30   |
    Then all types should be correctly converted
      | name:str | age:int | price:float | active:bool | created:date |
      | Alice    | 30      | 99.99       | true        | 2024-01-15   |
      | Bob      | 25      | 49.50       | false       | 2024-06-30   |

  Scenario: Nullable columns with null markers
    Given a table with nullable typed columns
      | name:str | age:int? | city:str? |
      | Alice    | 30       | NYC       |
      | Bob      | null     | N/A       |
      | Carol    |          |           |
    Then nullable columns should resolve nulls to None

  Scenario: Empty table with typed headers
    Given an empty typed table
      | name:str | age:int |
    Then the typed table should have 0 data rows

  Scenario: Single column table
    Given a single column table
      | name:str |
      | Alice    |
    Then the single column should have one entry "Alice"

  Scenario: Table with special characters
    Given a table with special characters
      | name:str | description:str |
      | Alice    | A "quoted" value |
      | Bob      | A 'single' value |
    Then special characters should be preserved
