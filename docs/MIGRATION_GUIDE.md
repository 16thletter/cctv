# Migration Guide

This guide helps you migrate from the old system to the new refactored architecture.

## Quick Migration Checklist

- [ ] Review new folder structure
- [ ] Update startup commands (use `main.py` instead of shell scripts)
- [ ] Test configuration loading
- [ ] Verify backward compatibility
- [ ] Update any custom code to use new interfaces (optional)

## Step-by-Step Migration

### Step 1: Review Changes

The refactoring maintains **backward compatibility** for most existing code. Key changes:

1. **New unified entry point**: `main.py` replaces shell scripts
2. **New detector architecture**: Plugin-based system (optional to use)
3. **Webhook service**: New feature for Rails integration
4. **Config manager**: Enhanced but backward compatible

### Step 2: Update Startup Commands

**Before:**
```bash
./scripts/run_with_gpu.sh --camera-id entrance
./scripts/start_api.sh
```

**After:**
```bash
python main.py run --camera-id entrance
python main.py api
```

### Step 3: Test Configuration

Your existing `config/config.yaml` should work as-is. The new system:
- Still uses the same config file format
- Still supports environment variables
- Adds new optional sections (webhooks, detectors)

Test configuration loading:
```bash
python scripts/test_integration.py
```

### Step 4: Verify Existing Functionality

All existing functionality should work:
- ✅ Person detection
- ✅ Face recognition
- ✅ Camera management
- ✅ Database operations
- ✅ API server

Test with:
```bash
# Health check
python main.py health

# List cameras
python main.py list-cameras

# Run cameras (same as before)
python main.py run
```

### Step 5: (Optional) Enable New Features

#### Enable Webhooks

Add to `config/config.yaml`:
```yaml
webhooks:
  enabled: true
  base_url: http://your-rails-api.com
  endpoints:
    person_in: /api/v1/events/person_in
    person_out: /api/v1/events/person_out
```

#### Enable Multiple Detectors

Add to `config/config.yaml`:
```yaml
detectors:
  enabled:
    - person
    - fire  # If you have fire detection model
```

## Backward Compatibility

### What Still Works

✅ **All existing imports**:
```python
from cctv.core.detector import PersonDetector  # Still works!
from cctv.utils.utils import load_config       # Still works!
```

✅ **All existing code**:
- `scripts/run_cameras.py` - Still works
- `scripts/cli/*.py` - Still works
- `src/cctv/api/server.py` - Still works

✅ **Configuration format**:
- Same YAML structure
- Same environment variables
- New sections are optional

### What's New (Optional to Use)

🆕 **New detector interface**:
```python
from cctv.detectors.person_detector import PersonDetector  # New way
from cctv.core.detector import PersonDetector              # Old way (still works)
```

🆕 **Detector factory**:
```python
from cctv.core.detector_factory import DetectorFactory
detector = DetectorFactory.create_detector('person', config)
```

🆕 **Webhook service**:
```python
from cctv.services.webhook_service import WebhookService
webhook_service.send_event('person_in', data, camera_id='entrance')
```

## Common Issues

### Issue: "Module not found"

**Solution**: Make sure you're running from project root and `src/` is in Python path:
```bash
# From project root
python main.py run
```

### Issue: "Config file not found"

**Solution**: Copy example config:
```bash
cp config/config.example.yaml config/config.yaml
# Edit config.yaml with your settings
```

### Issue: "Old code breaks"

**Solution**: The old code should still work. If it doesn't:
1. Check you're using the compatibility layer
2. Verify imports are correct
3. Run integration tests: `python scripts/test_integration.py`

## Gradual Migration Path

You don't need to migrate everything at once:

1. **Phase 1**: Use new entry point (`main.py`) but keep existing code
2. **Phase 2**: Gradually adopt new detector interface for new features
3. **Phase 3**: Enable webhooks when Rails backend is ready
4. **Phase 4**: Add new detectors using the plugin system

## Testing Your Migration

Run the integration test:
```bash
python scripts/test_integration.py
```

This will verify:
- ✅ All imports work
- ✅ Configuration loads correctly
- ✅ Detector factory works
- ✅ Backward compatibility maintained
- ✅ Webhook service initializes

## Rollback Plan

If you need to rollback:

1. **Keep using old scripts**: The old shell scripts still work
2. **Old imports still work**: `from cctv.core.detector import PersonDetector`
3. **Config format unchanged**: Your existing config.yaml works

## Getting Help

- Check `README.md` for usage
- See `docs/ARCHITECTURE.md` for design details
- See `docs/ADDING_DETECTORS.md` for extending the system
- Run `python main.py health` for diagnostics

## Next Steps After Migration

1. ✅ Test all existing functionality
2. ✅ Enable webhooks (if using Rails)
3. ✅ Add new detectors (mask, queue, etc.)
4. ✅ Update deployment scripts to use `main.py`
5. ✅ Monitor logs for any issues

---

**Remember**: The refactoring maintains backward compatibility. Your existing code should continue to work while you gradually adopt new features.

