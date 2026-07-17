Feature: Dynamic examples E2E

  @load_examples:csv:features/data/users.csv
  Scenario Outline: Load users from CSV
    Given a user with name "<name>" and email "<email>"
    Then the user "<name>" should have email "<email>"

    Examples:
      | name | email |
      | old  | old   |

  @load_examples:json:features/data/products.json
  Scenario Outline: Load products from JSON
    Given a product with name "<name>" and price "<price>"
    Then the product "<name>" should cost "<price>"

    Examples:
      | name | price |
      | old  | old   |
