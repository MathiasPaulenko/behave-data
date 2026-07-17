"""E2E steps for fixtures, builders, secrets, typed tables, and dynamic examples."""

from __future__ import annotations

import os
from datetime import date

from behave import given, then, when

from behave_data import typed_wrap

# --------------------------------------------------------------------------- #
# Fixtures & Builders
# --------------------------------------------------------------------------- #


@given("I need an admin user")
def step_need_admin(context):
    assert hasattr(context, "admin_user")
    context.current_user = context.admin_user


@then('the admin user should have role "{role}"')
def step_admin_role(context, role):
    assert context.current_user["role"] == role


@then('the admin user should have email "{email}"')
def step_admin_email(context, email):
    assert context.current_user["email"] == email


@given("I need a regular user")
def step_need_regular(context):
    loaded = getattr(context, "_behave_data_loaded", {})
    # Find any regular_user:* fixture that was loaded
    for key, val in loaded.items():
        if key.startswith("regular_user:"):
            context.current_user = val
            return
    raise AssertionError("No regular_user fixture loaded")


@then('the regular user should have name "{name}"')
def step_regular_name(context, name):
    assert context.current_user["name"] == name


@then('the regular user should have role "{role}"')
def step_regular_role(context, role):
    assert context.current_user["role"] == role


@given("I build a product")
def step_build_product(context):
    context.product = context.data.build("product")


@then('the product should have name "{name}"')
def step_product_name(context, name):
    assert context.product["name"] == name


@then("the product should have price {price:f}")
def step_product_price(context, price):
    assert abs(context.product["price"] - price) < 0.01


@given('I build a product with name "{name}" and price {price:f}')
def step_build_product_overrides(context, name, price):
    context.product = context.data.build("product", overrides={"name": name, "price": price})


@given("I build {n:d} products")
def step_build_multiple(context, n):
    context.products = context.data.build("product", count=n)


@then("I should have {n:d} products")
def step_count_products(context, n):
    assert len(context.products) == n


@then('each product should have name "{name}"')
def step_each_product_name(context, name):
    for p in context.products:
        assert p["name"] == name


@given("I register a cleanup function")
def step_register_cleanup(context):
    context.cleanup_flag = False

    def _cleanup():
        context.cleanup_flag = False

    if not hasattr(context, "_behave_data_cleanup_funcs"):
        context._behave_data_cleanup_funcs = []
    context._behave_data_cleanup_funcs.append(_cleanup)
    context.cleanup_flag = True


@then("the cleanup flag should be True")
def step_cleanup_flag(context):
    assert context.cleanup_flag is True


# --------------------------------------------------------------------------- #
# Secrets
# --------------------------------------------------------------------------- #


@given('I set environment variable "{var}" to "{value}"')
def step_set_env(context, var, value):
    os.environ[var] = value
    context._env_var = var


@when('I resolve the placeholder "{placeholder}"')
def step_resolve(context, placeholder):
    context.resolved = context.data.resolve(placeholder)


@then('the resolved value should be "{value}"')
def step_resolved_value(context, value):
    assert str(context.resolved) == value


@when('I resolve and mask the placeholder "{placeholder}"')
def step_resolve_and_mask(context, placeholder):
    raw = context.data.resolve(placeholder)
    context.resolved = raw
    context.masked = context.data.mask(raw)


@then('the masked value should be "{value}"')
def step_masked_value(context, value):
    assert str(context.masked) == value


@when("I resolve the value {val:d}")
def step_resolve_int(context, val):
    context.resolved = context.data.resolve(val)


# --------------------------------------------------------------------------- #
# Typed table edge cases
# --------------------------------------------------------------------------- #


@given("a table with all types")
def step_all_types(context):
    context.typed = typed_wrap(context.table).typed_dicts()


@then("all types should be correctly converted")
def step_check_all_types(context):
    expected = typed_wrap(context.table).typed_dicts()
    assert len(expected) == 2
    assert isinstance(expected[0]["name"], str)
    assert isinstance(expected[0]["age"], int)
    assert isinstance(expected[0]["price"], float)
    assert isinstance(expected[0]["active"], bool)
    assert isinstance(expected[0]["created"], date)
    assert expected[0]["active"] is True
    assert expected[1]["active"] is False
    assert expected[0]["created"] == date(2024, 1, 15)
    assert expected[1]["created"] == date(2024, 6, 30)


@given("a table with nullable typed columns")
def step_nullable_typed(context):
    context.typed = typed_wrap(context.table).typed_dicts()


@then("nullable columns should resolve nulls to None")
def step_check_nullable(context):
    rows = context.typed
    assert rows[0]["age"] == 30
    assert rows[0]["city"] == "NYC"
    assert rows[1]["age"] is None
    assert rows[1]["city"] is None
    assert rows[2]["age"] is None
    assert rows[2]["city"] is None


@given("an empty typed table")
def step_empty_typed(context):
    context.typed = typed_wrap(context.table)


@then("the typed table should have 0 data rows")
def step_zero_rows(context):
    assert len(context.typed.typed_dicts()) == 0


@given("a single column table")
def step_single_col(context):
    context.typed = typed_wrap(context.table).typed_dicts()


@then('the single column should have one entry "{value}"')
def step_single_entry(context, value):
    rows = context.typed
    assert len(rows) == 1
    assert rows[0]["name"] == value


@given("a table with special characters")
def step_special_chars(context):
    context.typed = typed_wrap(context.table).typed_dicts()


@then("special characters should be preserved")
def step_check_special(context):
    rows = context.typed
    assert "quoted" in rows[0]["description"]
    assert "single" in rows[1]["description"]


# --------------------------------------------------------------------------- #
# Dynamic examples
# --------------------------------------------------------------------------- #


@given('a user with name "{name}" and email "{email}"')
def step_user_with(context, name, email):
    context.current_name = name
    context.current_email = email


@then('the user "{name}" should have email "{email}"')
def step_user_email(context, name, email):
    assert context.current_name == name
    assert context.current_email == email


@given('a product with name "{name}" and price "{price}"')
def step_product_with(context, name, price):
    context.current_product_name = name
    context.current_product_price = price


@then('the product "{name}" should cost "{price}"')
def step_product_cost(context, name, price):
    assert context.current_product_name == name
    assert context.current_product_price == price
