"""
Tests for ConnectionTab integration with ProjectorDialog.

This module tests:
- SQL Server connection test button validation and execution
- Projector table management (add, edit, remove)
- Dialog integration (ProjectorDialog opens and closes correctly)
- Selection handling and button states
- Test connection workflows
"""

import pytest
from unittest.mock import MagicMock, patch, call
from PyQt6.QtWidgets import QMessageBox, QDialog, QTableWidgetItem
from PyQt6.QtCore import Qt

# Mark all tests as UI and integration tests
pytestmark = [pytest.mark.ui, pytest.mark.integration]


class TestSQLTestButton:
    """Tests for SQL Server connection test button."""

    def test_sql_test_button_exists(self, qapp, qtbot, mock_db_manager):
        """Test SQL test button is present in the UI."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._test_sql_btn is not None
        assert tab._test_sql_btn.isEnabled()

    def test_sql_test_button_validation_empty_server(self, qapp, qtbot, mock_db_manager):
        """Test SQL test button shows error when server field is empty."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Leave server empty
        tab._sql_server_edit.setText("")
        tab._sql_database_edit.setText("TestDB")

        with patch.object(QMessageBox, 'warning') as mock_warning:
            tab._test_sql_connection()

            # Should show warning
            assert mock_warning.called
            args = mock_warning.call_args[0]
            assert "required" in args[2].lower() or "server" in args[2].lower()

    def test_sql_test_button_validation_empty_database(self, qapp, qtbot, mock_db_manager):
        """Test SQL test button shows error when database field is empty."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Leave database empty
        tab._sql_server_edit.setText("192.168.1.100")
        tab._sql_database_edit.setText("")

        with patch.object(QMessageBox, 'warning') as mock_warning:
            tab._test_sql_connection()

            # Should show warning
            assert mock_warning.called
            args = mock_warning.call_args[0]
            assert "required" in args[2].lower() or "database" in args[2].lower()

    def test_sql_test_button_validation_sql_auth_no_username(self, qapp, qtbot, mock_db_manager):
        """Test SQL test button shows error when SQL auth selected but no username."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Set SQL Server authentication (not Windows)
        tab._sql_auth_combo.setCurrentIndex(1)  # SQL Server Auth
        tab._sql_server_edit.setText("192.168.1.100")
        tab._sql_database_edit.setText("TestDB")
        tab._sql_username_edit.setText("")

        with patch.object(QMessageBox, 'warning') as mock_warning:
            tab._test_sql_connection()

            # Should show warning
            assert mock_warning.called
            args = mock_warning.call_args[0]
            assert "username" in args[2].lower() and "required" in args[2].lower()

    def test_sql_test_button_success(self, qapp, qtbot, mock_db_manager):
        """Test SQL test button shows success message on successful connection."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Fill valid data
        tab._sql_server_edit.setText("192.168.1.100")
        tab._sql_database_edit.setText("TestDB")
        tab._sql_auth_combo.setCurrentIndex(0)  # Windows Auth

        # Mock successful connection
        with patch('src.database.sqlserver_manager.SQLServerManager') as mock_sql:
            mock_instance = MagicMock()
            mock_instance.test_connection.return_value = (True, "Connection successful")
            mock_sql.return_value = mock_instance

            with patch.object(QMessageBox, 'information') as mock_info:
                tab._test_sql_connection()

                # Should show success message
                assert mock_info.called
                assert mock_instance.test_connection.called

    def test_sql_test_button_failure(self, qapp, qtbot, mock_db_manager):
        """Test SQL test button shows error message on failed connection."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Fill valid data
        tab._sql_server_edit.setText("192.168.1.100")
        tab._sql_database_edit.setText("TestDB")
        tab._sql_auth_combo.setCurrentIndex(0)  # Windows Auth

        # Mock failed connection
        with patch('src.database.sqlserver_manager.SQLServerManager') as mock_sql:
            mock_instance = MagicMock()
            mock_instance.test_connection.return_value = (False, "Connection timeout")
            mock_sql.return_value = mock_instance

            with patch.object(QMessageBox, 'warning') as mock_warning:
                tab._test_sql_connection()

                # Should show warning message
                assert mock_warning.called
                args = mock_warning.call_args[0]
                assert "timeout" in args[2].lower() or "failed" in args[2].lower()

    def test_sql_test_button_exception_handling(self, qapp, qtbot, mock_db_manager):
        """Test SQL test button handles exceptions gracefully."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Fill valid data
        tab._sql_server_edit.setText("192.168.1.100")
        tab._sql_database_edit.setText("TestDB")

        # Mock exception during connection
        with patch('src.database.sqlserver_manager.SQLServerManager') as mock_sql:
            mock_sql.side_effect = Exception("Unexpected error")

            with patch.object(QMessageBox, 'critical') as mock_critical:
                tab._test_sql_connection()

                # Should show error message
                assert mock_critical.called

    def test_sql_test_button_sanitizes_password(self, qapp, qtbot, mock_db_manager):
        """Test SQL test button sanitizes password from error messages."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Fill valid data with password
        tab._sql_server_edit.setText("192.168.1.100")
        tab._sql_database_edit.setText("TestDB")
        tab._sql_auth_combo.setCurrentIndex(1)  # SQL Server Auth
        tab._sql_username_edit.setText("admin")
        tab._sql_password_edit.setText("SecretPassword123")

        # Mock exception with password in error message
        with patch('src.database.sqlserver_manager.SQLServerManager') as mock_sql:
            mock_sql.side_effect = Exception("Login failed for user 'admin' with password 'SecretPassword123'")

            with patch.object(QMessageBox, 'critical') as mock_critical:
                tab._test_sql_connection()

                # Verify password was sanitized
                assert mock_critical.called
                args = mock_critical.call_args[0]
                assert "SecretPassword123" not in args[2]
                assert "***" in args[2]


class TestProjectorTable:
    """Tests for projector table management."""

    def test_projector_table_exists(self, qapp, qtbot, mock_db_manager):
        """Test projector table is present in the UI."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        assert tab._projector_table is not None
        assert tab._projector_table.columnCount() == 4

    def test_projector_table_headers(self, qapp, qtbot, mock_db_manager):
        """Test projector table has correct headers."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Verify headers (may be translated)
        assert tab._projector_table.horizontalHeaderItem(0) is not None
        assert tab._projector_table.horizontalHeaderItem(1) is not None
        assert tab._projector_table.horizontalHeaderItem(2) is not None
        assert tab._projector_table.horizontalHeaderItem(3) is not None

    def test_projector_buttons_disabled_initially(self, qapp, qtbot, mock_db_manager):
        """Test edit/remove/test buttons are disabled when no selection."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Edit, remove, and test buttons should be disabled initially
        assert not tab._edit_projector_btn.isEnabled()
        assert not tab._remove_projector_btn.isEnabled()
        assert not tab._test_projector_btn.isEnabled()

        # Add button should be enabled
        assert tab._add_projector_btn.isEnabled()

    def test_projector_selection_enables_buttons(self, qapp, qtbot, mock_db_manager):
        """Test selecting a projector enables edit/remove/test buttons."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Add a row to the table
        tab._projector_table.insertRow(0)
        tab._projector_table.setItem(0, 0, QTableWidgetItem("Test Projector"))
        tab._projector_table.setItem(0, 1, QTableWidgetItem("192.168.1.100"))
        tab._projector_table.setItem(0, 2, QTableWidgetItem("4352"))
        tab._projector_table.setItem(0, 3, QTableWidgetItem("pjlink"))

        # Select the row
        tab._projector_table.selectRow(0)

        # Buttons should now be enabled
        assert tab._edit_projector_btn.isEnabled()
        assert tab._remove_projector_btn.isEnabled()
        assert tab._test_projector_btn.isEnabled()


class TestAddProjector:
    """Tests for adding projectors via ProjectorDialog."""

    def test_add_projector_dialog_opens(self, qapp, qtbot, mock_db_manager):
        """Test clicking add button opens ProjectorDialog."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        with patch('src.ui.dialogs.settings_tabs.connection_tab.ProjectorDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = QDialog.DialogCode.Rejected
            mock_dialog_class.return_value = mock_dialog

            # Click add button
            tab._add_projector_btn.click()

            # Dialog should have been created and shown
            assert mock_dialog_class.called
            assert mock_dialog.exec.called

    def test_add_projector_dialog_adds_to_table(self, qapp, qtbot, mock_db_manager):
        """Test accepting add dialog adds projector to table."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        initial_row_count = tab._projector_table.rowCount()

        with patch('src.ui.dialogs.settings_tabs.connection_tab.ProjectorDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
            mock_dialog.get_projector_data.return_value = {
                "proj_name": "New Projector",
                "proj_ip": "192.168.1.100",
                "proj_port": 4352,
                "proj_type": "pjlink",
            }
            mock_dialog_class.return_value = mock_dialog

            # Click add button
            tab._add_projector_btn.click()

            # Table should have one more row
            assert tab._projector_table.rowCount() == initial_row_count + 1

            # Verify data was added
            last_row = tab._projector_table.rowCount() - 1
            assert tab._projector_table.item(last_row, 0).text() == "New Projector"
            assert tab._projector_table.item(last_row, 1).text() == "192.168.1.100"
            assert tab._projector_table.item(last_row, 2).text() == "4352"
            assert tab._projector_table.item(last_row, 3).text() == "pjlink"

    def test_add_projector_dialog_rejected_does_not_add(self, qapp, qtbot, mock_db_manager):
        """Test rejecting add dialog does not add projector to table."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        initial_row_count = tab._projector_table.rowCount()

        with patch('src.ui.dialogs.settings_tabs.connection_tab.ProjectorDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = QDialog.DialogCode.Rejected
            mock_dialog_class.return_value = mock_dialog

            # Click add button
            tab._add_projector_btn.click()

            # Table should have same row count
            assert tab._projector_table.rowCount() == initial_row_count

    def test_add_projector_marks_dirty(self, qapp, qtbot, mock_db_manager):
        """Test adding projector marks tab as dirty (changes pending)."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Create a signal spy for dirty signal
        dirty_emitted = []
        tab.settings_changed.connect(lambda: dirty_emitted.append(True))

        with patch('src.ui.dialogs.settings_tabs.connection_tab.ProjectorDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
            mock_dialog.get_projector_data.return_value = {
                "proj_name": "New Projector",
                "proj_ip": "192.168.1.100",
                "proj_port": 4352,
                "proj_type": "pjlink",
            }
            mock_dialog_class.return_value = mock_dialog

            # Click add button
            tab._add_projector_btn.click()

            # Dirty signal should have been emitted
            assert len(dirty_emitted) > 0


class TestEditProjector:
    """Tests for editing projectors via ProjectorDialog."""

    def test_edit_projector_no_selection_does_nothing(self, qapp, qtbot, mock_db_manager):
        """Test edit button does nothing when no projector is selected."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        with patch('src.ui.dialogs.settings_tabs.connection_tab.ProjectorDialog') as mock_dialog_class:
            # Force edit button to be enabled for testing
            tab._edit_projector_btn.setEnabled(True)

            # Click edit button (should exit early due to no selection)
            tab._edit_projector()

            # Dialog should not have been created
            assert not mock_dialog_class.called

    def test_edit_projector_dialog_opens_with_data(self, qapp, qtbot, mock_db_manager):
        """Test edit dialog opens with existing projector data."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Add a projector to the table
        tab._projector_table.insertRow(0)
        tab._projector_table.setItem(0, 0, QTableWidgetItem("Existing Projector"))
        tab._projector_table.setItem(0, 1, QTableWidgetItem("192.168.1.100"))
        tab._projector_table.setItem(0, 2, QTableWidgetItem("4352"))
        tab._projector_table.setItem(0, 3, QTableWidgetItem("pjlink"))

        # Select the row
        tab._projector_table.selectRow(0)

        with patch('src.ui.dialogs.settings_tabs.connection_tab.ProjectorDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = QDialog.DialogCode.Rejected
            mock_dialog_class.return_value = mock_dialog

            # Click edit button
            tab._edit_projector()

            # Dialog should have been created with projector data
            assert mock_dialog_class.called
            call_kwargs = mock_dialog_class.call_args[1]
            assert call_kwargs["projector_data"]["proj_name"] == "Existing Projector"
            assert call_kwargs["projector_data"]["proj_ip"] == "192.168.1.100"

    def test_edit_projector_dialog_updates_table(self, qapp, qtbot, mock_db_manager):
        """Test accepting edit dialog updates projector in table."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Add a projector to the table
        tab._projector_table.insertRow(0)
        tab._projector_table.setItem(0, 0, QTableWidgetItem("Old Name"))
        tab._projector_table.setItem(0, 1, QTableWidgetItem("192.168.1.100"))
        tab._projector_table.setItem(0, 2, QTableWidgetItem("4352"))
        tab._projector_table.setItem(0, 3, QTableWidgetItem("pjlink"))

        # Select the row
        tab._projector_table.selectRow(0)

        with patch('src.ui.dialogs.settings_tabs.connection_tab.ProjectorDialog') as mock_dialog_class:
            mock_dialog = MagicMock()
            mock_dialog.exec.return_value = QDialog.DialogCode.Accepted
            mock_dialog.get_projector_data.return_value = {
                "proj_name": "Updated Name",
                "proj_ip": "192.168.1.101",
                "proj_port": 4353,
                "proj_type": "pjlink",
            }
            mock_dialog_class.return_value = mock_dialog

            # Click edit button
            tab._edit_projector()

            # Table should be updated
            assert tab._projector_table.item(0, 0).text() == "Updated Name"
            assert tab._projector_table.item(0, 1).text() == "192.168.1.101"
            assert tab._projector_table.item(0, 2).text() == "4353"


class TestRemoveProjector:
    """Tests for removing projectors."""

    def test_remove_projector_no_selection_does_nothing(self, qapp, qtbot, mock_db_manager):
        """Test remove button does nothing when no projector is selected."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        with patch.object(QMessageBox, 'question') as mock_question:
            # Force remove button to be enabled for testing
            tab._remove_projector_btn.setEnabled(True)

            # Click remove button (should exit early due to no selection)
            tab._remove_projector()

            # Confirmation dialog should not have been shown
            assert not mock_question.called

    def test_remove_projector_shows_confirmation(self, qapp, qtbot, mock_db_manager):
        """Test removing projector shows confirmation dialog."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Add a projector to the table
        tab._projector_table.insertRow(0)
        tab._projector_table.setItem(0, 0, QTableWidgetItem("Test Projector"))
        tab._projector_table.setItem(0, 1, QTableWidgetItem("192.168.1.100"))
        tab._projector_table.setItem(0, 2, QTableWidgetItem("4352"))
        tab._projector_table.setItem(0, 3, QTableWidgetItem("pjlink"))

        # Select the row
        tab._projector_table.selectRow(0)

        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.No) as mock_question:
            # Click remove button
            tab._remove_projector()

            # Confirmation dialog should have been shown
            assert mock_question.called
            args = mock_question.call_args[0]
            assert "Test Projector" in args[2]

    def test_remove_projector_confirmed_removes_row(self, qapp, qtbot, mock_db_manager):
        """Test confirming removal actually removes the row."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Add a projector to the table
        tab._projector_table.insertRow(0)
        tab._projector_table.setItem(0, 0, QTableWidgetItem("Test Projector"))
        tab._projector_table.setItem(0, 1, QTableWidgetItem("192.168.1.100"))
        tab._projector_table.setItem(0, 2, QTableWidgetItem("4352"))
        tab._projector_table.setItem(0, 3, QTableWidgetItem("pjlink"))

        initial_count = tab._projector_table.rowCount()

        # Select the row
        tab._projector_table.selectRow(0)

        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            # Click remove button
            tab._remove_projector()

            # Row should be removed
            assert tab._projector_table.rowCount() == initial_count - 1

    def test_remove_projector_cancelled_keeps_row(self, qapp, qtbot, mock_db_manager):
        """Test cancelling removal keeps the row."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Add a projector to the table
        tab._projector_table.insertRow(0)
        tab._projector_table.setItem(0, 0, QTableWidgetItem("Test Projector"))
        tab._projector_table.setItem(0, 1, QTableWidgetItem("192.168.1.100"))
        tab._projector_table.setItem(0, 2, QTableWidgetItem("4352"))
        tab._projector_table.setItem(0, 3, QTableWidgetItem("pjlink"))

        initial_count = tab._projector_table.rowCount()

        # Select the row
        tab._projector_table.selectRow(0)

        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.No):
            # Click remove button but cancel
            tab._remove_projector()

            # Row should still be there
            assert tab._projector_table.rowCount() == initial_count


class TestProjectorConnectionTest:
    """Tests for testing individual projector connections."""

    def test_test_projector_no_selection_shows_warning(self, qapp, qtbot, mock_db_manager):
        """Test testing projector with no selection shows warning."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        with patch.object(QMessageBox, 'warning') as mock_warning:
            # Force test button to be enabled for testing
            tab._test_projector_btn.setEnabled(True)

            # Click test button with no selection
            tab._test_projector_connection()

            # Warning should have been shown
            assert mock_warning.called
            args = mock_warning.call_args[0]
            assert "select" in args[2].lower()

    def test_test_projector_with_selection(self, qapp, qtbot, mock_db_manager):
        """Test testing projector with valid selection."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Add a projector to the table
        tab._projector_table.insertRow(0)
        tab._projector_table.setItem(0, 0, QTableWidgetItem("Test Projector"))
        tab._projector_table.setItem(0, 1, QTableWidgetItem("192.168.1.100"))
        tab._projector_table.setItem(0, 2, QTableWidgetItem("4352"))
        tab._projector_table.setItem(0, 3, QTableWidgetItem("pjlink"))

        # Select the row
        tab._projector_table.selectRow(0)

        # Note: The actual test implementation is incomplete in the source,
        # so we just verify the method can be called without errors
        with patch.object(QMessageBox, 'information'):
            # This will test the method execution path
            # Actual implementation may show "not implemented" message
            tab._test_projector_connection()


class TestAuthenticationTypeToggle:
    """Tests for SQL authentication type toggle."""

    def test_auth_type_windows_disables_credentials(self, qapp, qtbot, mock_db_manager):
        """Test selecting Windows auth disables username/password fields."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Select Windows Authentication
        tab._sql_auth_combo.setCurrentIndex(0)

        # Username and password should be disabled
        assert not tab._sql_username_edit.isEnabled()
        assert not tab._sql_password_edit.isEnabled()

    def test_auth_type_sql_enables_credentials(self, qapp, qtbot, mock_db_manager):
        """Test selecting SQL auth enables username/password fields."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Select SQL Server Authentication
        tab._sql_auth_combo.setCurrentIndex(1)

        # Username and password should be enabled
        assert tab._sql_username_edit.isEnabled()
        assert tab._sql_password_edit.isEnabled()

    def test_auth_type_change_marks_dirty(self, qapp, qtbot, mock_db_manager):
        """Test changing authentication type marks tab as dirty."""
        from src.ui.dialogs.settings_tabs.connection_tab import ConnectionTab

        tab = ConnectionTab(mock_db_manager)
        qtbot.addWidget(tab)

        # Create a signal spy for dirty signal
        dirty_emitted = []
        tab.settings_changed.connect(lambda: dirty_emitted.append(True))

        # Change auth type
        tab._sql_auth_combo.setCurrentIndex(1)

        # Dirty signal should have been emitted
        assert len(dirty_emitted) > 0
