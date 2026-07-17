Feature: Typed table conversion
  Scenario: Table with int, float, bool columns
    Given a table with typed columns
      | name:str | doors:int | price:float | active:bool |
      | Alice    | 3         | 19.99       | true        |
      | Bob      | 5         | 29.50       | false       |
    Then the typed dicts should have correct types
