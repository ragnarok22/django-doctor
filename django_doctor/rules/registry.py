from __future__ import annotations

from django_doctor.core.config import VALID_CATEGORIES
from django_doctor.rules.architecture.large_files import LargeFileRule
from django_doctor.rules.base import Rule
from django_doctor.rules.drf.permissions import AllowAnyPermissionRule
from django_doctor.rules.drf.serializers import SerializerFieldsAllRule
from django_doctor.rules.security.allowed_hosts import AllowedHostsWildcardRule
from django_doctor.rules.security.cors import CorsAllowAllRule
from django_doctor.rules.security.debug_true import DebugTrueRule
from django_doctor.rules.security.secret_key import SecretKeyHardcodedRule
from django_doctor.rules.testing.no_tests import NoTestsDetectedRule


def all_rules() -> list[Rule]:
    return [
        DebugTrueRule(),
        SecretKeyHardcodedRule(),
        AllowedHostsWildcardRule(),
        CorsAllowAllRule(),
        LargeFileRule(),
        SerializerFieldsAllRule(),
        AllowAnyPermissionRule(),
        NoTestsDetectedRule(),
    ]


def get_rules(categories: list[str] | None = None) -> list[Rule]:
    rules = all_rules()
    if not categories:
        return rules
    unknown = sorted(set(categories) - VALID_CATEGORIES)
    if unknown:
        valid = ", ".join(sorted(VALID_CATEGORIES))
        raise ValueError(f"Unknown category: {', '.join(unknown)}. Valid categories: {valid}")
    selected = set(categories)
    return [rule for rule in rules if rule.category in selected]


def implemented_rule_ids() -> list[str]:
    return [rule.id for rule in all_rules()]
