# Unused Files Archive

This directory contains files that served their purpose during development but are no longer actively used in the production application.

## Categories

### Debug Scripts (check_*.py)
Scripts used to diagnose specific issues during development:
- `check_database_integrity.py` - Database integrity verification
- `check_distances.py` - Distance calculation testing
- `check_fulfillment.py` - Fulfillment logic testing
- `check_mike_locations.py` - Multi-location matching debugging
- `check_requester_history.py` - History query debugging
- `check_request_8.py` - Specific request debugging
- `check_timezone_consistency.py` - Timezone implementation testing
- `check_user_data.py` - User data verification
- `check_user_locations.py` - Location data verification

### Fix Scripts (fix_*.py)
One-time scripts to resolve specific database or data issues:
- `fix_database.py` - Database schema/data fixes
- `fix_multiple_donations.py` - Fixed duplicate donation tracking
- `fix_request_7.py` - Resolved specific request issues
- `fix_user_timezones.py` - Timezone data migration

### Migration Scripts
Database schema migration utilities:
- `add_timezone_column.py` - Added timezone support
- `migrate_add_fulfillment_fields.py` - Added fulfillment tracking

### Test Scripts (test_*.py)
Testing utilities for specific features:
- `test_donor_notifications.py` - Notification system testing
- `test_ml_models.py` - ML model validation
- `test_timezone_calculations.py` - Timezone logic testing

### Debug Utilities
General debugging tools:
- `debug_query.py` - Query debugging
- `simulate_history_query.py` - History simulation
- `verify_db_schema.py` - Schema verification
- `investigate_request_7.py` - Request investigation
- `reset_users.py` - User data reset utility

### Unused Feature Modules
Features that were implemented but not integrated into the main application:
- `adaptive_training.py` - Adaptive ML training (8.6KB)
- `demand_forecast.py` - Demand forecasting (10.4KB)
- `escalation_service.py` - Request escalation system (4.8KB)
- `routing_service.py` - Advanced routing algorithms (5.4KB)
- `timezone_utils.py` - Timezone utilities (simplified in production) (4.1KB)

## Why Archive?

These files are preserved for:
1. **Historical Reference** - Understanding how issues were resolved
2. **Future Debugging** - Similar issues may require similar approaches
3. **Code Examples** - Useful patterns for future development
4. **Audit Trail** - Track evolution of the codebase

## Note

**Do NOT import or use these files in production.** They are archived only and may contain outdated logic or dependencies.
