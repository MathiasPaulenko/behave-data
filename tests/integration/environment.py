"""Behave environment for integration tests."""

from __future__ import annotations

from behave_data import (
    after_scenario_hook,
    before_feature_hook,
    before_scenario_hook,
    before_step_hook,
    setup_data,
)
from behave_data.builders import data_builder
from behave_data.fixtures import data_fixture


@data_fixture("admin_user")
def admin_user():
    return {"name": "Admin", "role": "admin", "email": "admin@test.com"}


@data_fixture("regular_user", params=["alice", "bob"])
def regular_user(param):
    return {"name": param, "role": "user"}


@data_builder("product")
def product(overrides):
    return {"name": "Widget", "price": 9.99, **overrides}


def before_all(context):
    setup_data(context)


def before_feature(context, feature):
    before_feature_hook(context, feature)


def before_scenario(context, scenario):
    before_scenario_hook(context, scenario)


def before_step(context, step):
    before_step_hook(context, step)


def after_scenario(context, scenario):
    after_scenario_hook(context, scenario)
