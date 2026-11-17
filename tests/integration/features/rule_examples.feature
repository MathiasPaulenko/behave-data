Feature: Dynamic examples inside a Rule

  Rule: Users from CSV inside a rule
    @load_examples:csv:users.csv
    Scenario Outline: Load users under a rule
      Given a user with name "<name>" and email "<email>"
      Then the loaded user "<name>" should have email "<email>"

      Examples:
        | name | email |
        | old  | old   |
