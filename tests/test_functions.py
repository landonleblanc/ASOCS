import pytest
import json

def test_load_settings(tmp_path):
    # Create a temporary settings.json file
    settings_file = tmp_path / 'settings.json'
    
    # Test case 1: settings.json exists
    settings = {'control_temp': 50, 'start_time': 660, 'end_time': 1020}
    with open(settings_file, 'w') as f:
        json.dump(settings, f)
    
    loaded_settings, success = load_settings()
    assert loaded_settings == settings
    assert success == True
    
    # Test case 2: settings.json does not exist
    settings_file.unlink()
    
    loaded_settings, success = load_settings()
    assert loaded_settings == settings
    assert success == False

