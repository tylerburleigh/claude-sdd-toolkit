"""Unit tests for SDD configuration loading."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from claude_skills.common.sdd_config import (
    load_sdd_config,
    DEFAULT_SDD_CONFIG,
    get_sdd_setting,
    get_config_path,
    _validate_sdd_config
)


class TestConfigDefaults:
    """Test default configuration values."""

    def test_default_config_structure(self):
        """Verify DEFAULT_SDD_CONFIG has correct structure."""
        assert 'output' in DEFAULT_SDD_CONFIG
        assert 'json' in DEFAULT_SDD_CONFIG['output']
        assert 'compact' in DEFAULT_SDD_CONFIG['output']

    def test_default_values(self):
        """Verify default values are correct."""
        assert DEFAULT_SDD_CONFIG['output']['json'] is True
        assert DEFAULT_SDD_CONFIG['output']['compact'] is True


class TestConfigLoading:
    """Test configuration loading and precedence."""

    @patch('claude_skills.common.sdd_config.get_config_path')
    def test_load_with_no_config_file(self, mock_get_path):
        """Test loading when no config file exists - should use defaults."""
        mock_get_path.return_value = None

        config = load_sdd_config()

        assert config == DEFAULT_SDD_CONFIG
        assert config['output']['json'] is True
        assert config['output']['compact'] is True

    @patch('claude_skills.common.sdd_config.get_config_path')
    @patch('builtins.open', new_callable=mock_open, read_data='{"output": {"json": false, "compact": false}}')
    def test_load_with_custom_config(self, mock_file, mock_get_path):
        """Test loading with custom configuration."""
        mock_get_path.return_value = Path('/fake/.claude/sdd_config.json')

        config = load_sdd_config()

        assert config['output']['json'] is False
        assert config['output']['compact'] is False

    @patch('claude_skills.common.sdd_config.get_config_path')
    @patch('builtins.open', new_callable=mock_open, read_data='{"output": {"json": false}}')
    def test_load_with_partial_config(self, mock_file, mock_get_path):
        """Test loading with partial configuration - missing fields use defaults."""
        mock_get_path.return_value = Path('/fake/.claude/sdd_config.json')

        config = load_sdd_config()

        # json is overridden
        assert config['output']['json'] is False
        # compact falls back to default
        assert config['output']['compact'] is True

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.cwd')
    def test_project_config_precedence_over_global(self, mock_cwd, mock_exists):
        """Test project config takes precedence over global config."""
        mock_cwd.return_value = Path('/project')

        # Only project config exists
        def exists_side_effect(self):
            return str(self) == '/project/.claude/sdd_config.json'

        with patch.object(Path, 'exists', exists_side_effect):
            config_path = get_config_path()
            assert config_path == Path('/project/.claude/sdd_config.json')


class TestConfigValidation:
    """Test configuration validation and error handling."""

    def test_validate_with_valid_config(self):
        """Test validation with valid configuration."""
        config = {
            'output': {
                'json': True,
                'compact': False
            }
        }

        validated = _validate_sdd_config(config)

        assert validated['output']['json'] is True
        assert validated['output']['compact'] is False

    def test_validate_with_invalid_types(self):
        """Test validation with invalid types - should use defaults."""
        config = {
            'output': {
                'json': 'true',  # Should be bool, not string
                'compact': 1  # Should be bool, not int
            }
        }

        validated = _validate_sdd_config(config)

        # Invalid types fall back to defaults
        assert validated['output']['json'] is True  # Default
        assert validated['output']['compact'] is True  # Default

    def test_validate_with_unknown_keys(self):
        """Test validation with unknown keys - should be ignored."""
        config = {
            'output': {
                'json': True,
                'compact': True
            },
            'unknown_key': 'value'
        }

        validated = _validate_sdd_config(config)

        # Known keys are validated
        assert validated['output']['json'] is True
        # Unknown keys are not in result
        assert 'unknown_key' not in validated

    @patch('claude_skills.common.sdd_config.get_config_path')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_load_with_invalid_json(self, mock_file, mock_get_path):
        """Test loading with invalid JSON - should fall back to defaults."""
        mock_get_path.return_value = Path('/fake/.claude/sdd_config.json')

        config = load_sdd_config()

        # Should fall back to defaults on JSON error
        assert config == DEFAULT_SDD_CONFIG

    @patch('claude_skills.common.sdd_config.get_config_path')
    @patch('builtins.open', new_callable=mock_open, read_data='null')
    def test_load_with_null_config(self, mock_file, mock_get_path):
        """Test loading with null/empty config - should use defaults."""
        mock_get_path.return_value = Path('/fake/.claude/sdd_config.json')

        config = load_sdd_config()

        # Should fall back to defaults
        assert config == DEFAULT_SDD_CONFIG

    @patch('claude_skills.common.sdd_config.get_config_path')
    def test_load_with_file_read_error(self, mock_get_path):
        """Test loading when file can't be read - should use defaults."""
        mock_get_path.return_value = Path('/fake/.claude/sdd_config.json')

        with patch('builtins.open', side_effect=IOError('Permission denied')):
            config = load_sdd_config()

        # Should fall back to defaults on I/O error
        assert config == DEFAULT_SDD_CONFIG


class TestGetSddSetting:
    """Test get_sdd_setting helper function."""

    @patch('claude_skills.common.sdd_config.load_sdd_config')
    def test_get_simple_setting(self, mock_load):
        """Test getting a simple nested setting."""
        mock_load.return_value = {'output': {'json': True, 'compact': False}}

        value = get_sdd_setting('output.json')

        assert value is True

    @patch('claude_skills.common.sdd_config.load_sdd_config')
    def test_get_nested_setting(self, mock_load):
        """Test getting deeply nested setting."""
        mock_load.return_value = {'output': {'json': False, 'compact': True}}

        value = get_sdd_setting('output.compact')

        assert value is True

    @patch('claude_skills.common.sdd_config.load_sdd_config')
    def test_get_missing_setting_with_default(self, mock_load):
        """Test getting missing setting with custom default."""
        mock_load.return_value = {'output': {'json': True}}

        value = get_sdd_setting('output.missing', default='custom_default')

        assert value == 'custom_default'

    @patch('claude_skills.common.sdd_config.load_sdd_config')
    def test_get_missing_setting_without_default(self, mock_load):
        """Test getting missing setting falls back to DEFAULT_SDD_CONFIG."""
        mock_load.return_value = {'output': {'json': False}}

        # 'compact' is missing, should get from DEFAULT_SDD_CONFIG
        value = get_sdd_setting('output.compact')

        assert value == DEFAULT_SDD_CONFIG['output']['compact']


class TestConfigPath:
    """Test configuration path resolution."""

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.cwd')
    def test_finds_project_config_in_cwd(self, mock_cwd, mock_exists):
        """Test finding project config in current directory."""
        mock_cwd.return_value = Path('/project')

        def exists_side_effect(self):
            return str(self) == '/project/.claude/sdd_config.json'

        with patch.object(Path, 'exists', exists_side_effect):
            config_path = get_config_path()
            assert config_path == Path('/project/.claude/sdd_config.json')

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.cwd')
    @patch('pathlib.Path.home')
    def test_finds_global_config_when_no_project(self, mock_home, mock_cwd, mock_exists):
        """Test finding global config when no project config exists."""
        mock_cwd.return_value = Path('/project')
        mock_home.return_value = Path('/home/user')

        def exists_side_effect(self):
            return str(self) == '/home/user/.claude/sdd_config.json'

        with patch.object(Path, 'exists', exists_side_effect):
            config_path = get_config_path()
            assert config_path == Path('/home/user/.claude/sdd_config.json')

    @patch('pathlib.Path.exists')
    def test_returns_none_when_no_config_found(self, mock_exists):
        """Test returns None when no config file exists."""
        mock_exists.return_value = False

        config_path = get_config_path()

        assert config_path is None
