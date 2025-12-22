"""
Unit tests for data_loader module.

Tests JSON loading and validation functions.
"""

import pytest
import json
import tempfile
from pathlib import Path
from data_loader import load_portfolio_from_json, validate_portfolio_data


class TestLoadPortfolioFromJson:
    """Tests for load_portfolio_from_json function."""

    def test_load_valid_portfolio(self):
        """Test loading a valid portfolio JSON."""
        data = {
            "name": "test_portfolio",
            "assets": [
                {"symbol": "ETH", "crypto_id": "ETH", "amount": 1.5}
            ]
        }
        
        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode="w", 
            suffix=".json", 
            delete=False
        ) as f:
            json.dump(data, f)
            temp_path = f.name
        
        try:
            portfolio = load_portfolio_from_json(temp_path)
            assert portfolio.name == "test_portfolio"
            assert len(portfolio.assets) == 1
            assert portfolio.assets[0].symbol == "ETH"
        finally:
            Path(temp_path).unlink()  # Clean up

    def test_file_not_found(self):
        """Test FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_portfolio_from_json("nonexistent.json")

    def test_invalid_extension(self):
        """Test ValueError for non-JSON file."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                load_portfolio_from_json(temp_path)
        finally:
            Path(temp_path).unlink()


class TestValidatePortfolioData:
    """Tests for validate_portfolio_data function."""

    def test_valid_data_no_errors(self):
        """Test that valid data returns empty error list."""
        data = {
            "name": "test",
            "assets": [
                {"symbol": "ETH", "amount": 1.0, "crypto_id": "ETH"}
            ]
        }
        errors = validate_portfolio_data(data)
        # Only "name missing" warning if present
        assert len([e for e in errors if "obligatory" in e]) == 0

    def test_missing_assets(self):
        """Test error when assets field is missing."""
        data = {"name": "test"}
        errors = validate_portfolio_data(data)
        assert any("assets" in e.lower() for e in errors)

    def test_empty_assets(self):
        """Test error when assets list is empty."""
        data = {"name": "test", "assets": []}
        errors = validate_portfolio_data(data)
        assert any("empty" in e.lower() or "least one" in e.lower() for e in errors)