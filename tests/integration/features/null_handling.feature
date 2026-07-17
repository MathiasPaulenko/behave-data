Feature: Null handling with various markers
  Scenario: Cells with empty string, null, and N/A markers
    Given a table with null markers
      | name:str | age:int? | city:str? |
      | Alice    | 30       | NYC       |
      | null     | N/A      |           |
    Then null cells should be resolved to None
