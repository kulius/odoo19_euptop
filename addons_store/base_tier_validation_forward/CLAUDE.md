# Base Tier Validation Forward Module (OCA)

## Module Information
- **Name**: Base Tier Validation Forward
- **Version**: 19.0.2.0.0
- **License**: AGPL-3
- **Author**: Ecosoft, Odoo Community Association (OCA)
- **Maintainer**: kittiu
- **Category**: Tools
- **Development Status**: Alpha

## Purpose
Adds forward/delegation functionality to the tier validation process. Allows reviewers to forward their review responsibility to another user instead of approving or rejecting.

## Dependencies
- `base_tier_validation`

## Key Features

### Forward Option
Reviewers can forward their pending review to another user:
- Delegate review responsibility
- Keep audit trail of forwarding
- Notify new reviewer

### Use Cases
1. **Delegation**: Reviewer is on vacation
2. **Escalation**: Need higher authority review
3. **Reassignment**: Wrong reviewer assigned
4. **Expertise**: Forward to subject matter expert

## Data Files
- `security/ir.model.access.csv`: Access control
- `data/mail_data.xml`: Email templates for forward notifications
- `views/tier_definition_view.xml`: Extended tier definition views
- `wizard/forward_wizard_view.xml`: Forward wizard interface
- `templates/tier_validation_templates.xml`: QWeb templates

## Frontend Assets
```python
'web.assets_backend': [
    "base_tier_validation_forward/static/src/xml/tier_review_template.xml",
]
```

## Wizard
Forward wizard allows:
- Select target user
- Add forward reason/comment
- Notify original and new reviewer

## Workflow
1. Review is pending for User A
2. User A clicks "Forward"
3. Wizard opens to select User B
4. Forward reason is recorded
5. User B receives notification
6. User A is removed from reviewers
7. User B can now approve/reject

## Views Extended
- Tier definition form with forward options
- Review template with forward button
- Forward wizard form

## Email Notifications
- Template for forward notification
- Includes original reviewer, new reviewer, reason

## Uninstall Hook
```python
"uninstall_hook": "uninstall_hook"
```
Cleanup function when module is uninstalled.

## Odoo 19 Compliance
- Upgraded from Odoo 18 to Odoo 19
- Version: 19.0.2.0.0
- Proper license field in manifest
- Modern view syntax

## Integration with base_tier_validation
Extends the standard tier validation buttons and review process:
1. Adds "Forward" button alongside Approve/Reject
2. Extends tier.review model with forward tracking
3. Modifies review assignment logic

## Best Practices
1. Set clear policies on when forwarding is allowed
2. Limit forward chain depth if needed
3. Track forward history for audit
4. Consider approval deadlines with forwards
