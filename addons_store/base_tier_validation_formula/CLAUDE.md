# Base Tier Validation Formula Module (OCA)

## Module Information
- **Name**: Base Tier Validation Formula
- **Version**: 19.0.1.0.0
- **License**: AGPL-3
- **Author**: Creu Blanca, Odoo Community Association (OCA)
- **Category**: Tools
- **Development Status**: Mature

## Purpose
Extends base_tier_validation to allow Python formulas for dynamic reviewer assignment. Instead of static reviewer groups, you can write Python expressions to determine who should review based on record data.

## Dependencies
- `base_tier_validation`

## Key Features

### Dynamic Reviewer Assignment
Allows writing Python code to dynamically determine reviewers based on:
- Record field values
- Related record data
- User/employee relationships
- Custom business logic

### Formula Fields
Extends `tier.definition` with formula capabilities:
- `python_code`: Field for Python expression
- `reviewer_expression`: Python code that returns reviewer users

## Usage Example

### Formula for Department Manager Review
```python
# Review by the employee's department manager
result = record.department_id.manager_id.user_id
```

### Formula for Amount-Based Reviewer
```python
# Different reviewer based on amount
if record.amount_total > 10000:
    result = env.ref('base.user_admin')
else:
    result = record.user_id.manager_id
```

### Formula for Multi-Level Approval
```python
# Get all managers up the hierarchy
result = env['res.users']
manager = record.employee_id.parent_id
while manager:
    result |= manager.user_id
    manager = manager.parent_id
```

## Views
- `views/tier_definition_view.xml`: Extended tier definition form with formula fields

## Technical Notes

### Safe Eval Context
The formula is executed in a safe eval context with access to:
- `record`: Current record being validated
- `env`: Odoo environment
- `user`: Current user
- Standard Python functions

### Security Considerations
- Formulas should be created by administrators only
- Code is executed with elevated privileges
- Input validation recommended

## Odoo 19 Compliance
- Upgraded from Odoo 18 to Odoo 19
- Version: 19.0.1.0.0
- Proper license field in manifest

## Integration with base_tier_validation
This module extends tier definitions to use formulas:
1. Create tier definition
2. Enable formula mode
3. Write Python expression
4. Expression evaluates during validation
5. Returns computed reviewer(s)

## Best Practices
1. Keep formulas simple and readable
2. Handle edge cases (empty relationships)
3. Always return `res.users` recordset
4. Test formulas thoroughly before production
5. Document formula logic in tier definition
