# Base Tier Validation Module (OCA)

## Module Information
- **Name**: Base Tier Validation
- **Version**: 19.0.3.1.0
- **License**: AGPL-3
- **Author**: ForgeFlow, Odoo Community Association (OCA)
- **Maintainer**: LoisRForgeFlow
- **Category**: Tools
- **Development Status**: Mature

## Purpose
Implements a validation process based on tiers. This is an abstract model that can be inherited by any other model to add multi-tier approval workflows. It provides configurable approval chains, reviewers, and notification systems.

## Dependencies
- `mail`

## Key Models

### tier.validation (Abstract)
**File**: `models/tier_validation.py`

Abstract model providing tier validation functionality. Inherit this in your models to enable approval workflows.

**Key Attributes**:
```python
_tier_validation_buttons_xpath = "/form/header/button[last()]"
_tier_validation_manual_config = True
_state_field = "state"
_state_from = ["draft"]
_state_to = ["confirmed"]
_cancel_state = "cancel"
```

**Key Fields**:
- `review_ids`: One2many to tier.review
- `validated`: Computed boolean
- `rejected`: Computed boolean
- `validation_status`: Selection (no, waiting, pending, rejected, validated)
- `reviewer_ids`: Many2many computed reviewers
- `can_review`: Boolean computed for current user
- `has_comment`: Boolean for comment capability
- `need_validation`: Boolean computed

**Key Methods**:
- `request_validation()`: Creates tier reviews
- `validate_tier()`: Approves current tier
- `reject_tier()`: Rejects current tier
- `restart_validation()`: Resets validation process
- `evaluate_tier()`: Checks if tier definition applies
- `_validate_tier()`: Internal validation logic
- `_rejected_tier()`: Internal rejection logic

### tier.definition
**File**: `models/tier_definition.py`

Defines approval tiers with criteria and reviewers.

### tier.review
**File**: `models/tier_review.py`

Individual review records for validation process.

### tier.validation.exception
**File**: `models/tier_validation_exception.py`

Field exceptions during validation (allowed writes).

### res.config.settings
**File**: `models/res_config_settings.py`

System configuration for tier validation.

## Validation States
```python
validation_status = fields.Selection([
    ("no", "Without validation"),
    ("waiting", "Waiting"),
    ("pending", "Pending"),
    ("rejected", "Rejected"),
    ("validated", "Validated"),
])
```

## Write Protection
The module protects records during validation:
- `_check_allow_write_under_validation()`: Fields allowed during validation
- `_check_allow_write_after_validation()`: Fields allowed after validation
- `_get_validation_exceptions()`: Get exception field list

## Notifications
Message subtypes for notifications:
- `mt_tier_validation_requested`: Review requested
- `mt_tier_validation_accepted`: Review accepted
- `mt_tier_validation_rejected`: Review rejected
- `mt_tier_validation_restarted`: Validation restarted

## Frontend Assets
```python
'web.assets_backend': [
    "base_tier_validation/static/src/components/**/*",
    "base_tier_validation/static/src/js/**/*",
]
```

## Wizards
- `wizard/comment_wizard.py`: Add comment during approve/reject

## Usage Example
```python
class MyModel(models.Model):
    _name = 'my.model'
    _inherit = ['tier.validation', 'mail.thread']

    _state_field = "state"
    _state_from = ["draft"]
    _state_to = ["approved"]
    _cancel_state = "cancel"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled'),
    ], default='draft')
```

## Migration
- `migrations/19.0.2.1.0/pre-migration.py`: Pre-migration script for v19

## Tests
- `tests/test_tier_validation.py`: Main validation tests
- `tests/test_tier_validation_reminder.py`: Reminder tests
- `tests/tier_validation_tester.py`: Test model
- `tests/common.py`: Common test utilities

## Odoo 19 Compliance
- Upgraded from Odoo 18 to Odoo 19
- Version: 19.0.3.1.0
- Uses `SQL` from `odoo.tools` for raw queries
- Modern view attribute syntax
