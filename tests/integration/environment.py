"""Behave environment for integration tests."""

from __future__ import annotations

from behave_data import setup_data
from behave_data.hooks import before_step_hook


def before_all(context):
    setup_data(context)


def before_step(context, step):
    before_step_hook(context, step)
