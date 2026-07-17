Feature: Fixtures and builders E2E

  @needs_data:admin_user
  Scenario: Admin user fixture is available via needs_data tag
    Given I need an admin user
    Then the admin user should have role "admin"
    And the admin user should have email "admin@test.com"

  @needs_data:regular_user:alice
  Scenario: Parametrized fixture is available via needs_data tag
    Given I need a regular user
    Then the regular user should have name "alice"
    And the regular user should have role "user"

  Scenario: Build a single product via DataManager
    Given I build a product
    Then the product should have name "Widget"
    And the product should have price 9.99

  Scenario: Build a product with overrides
    Given I build a product with name "Gadget" and price 19.99
    Then the product should have name "Gadget"
    And the product should have price 19.99

  Scenario: Build multiple products
    Given I build 3 products
    Then I should have 3 products
    And each product should have name "Widget"

  @cleanup_after
  Scenario: Cleanup after scenario
    Given I register a cleanup function
    Then the cleanup flag should be True
    # After scenario, cleanup runs automatically via after_scenario_hook
