"""
Enhanced Tooltip Widget for Projector Control Application.

Provides context-aware tooltips with:
- Rich HTML content formatting
- Optional icons and titles
- Full RTL support for Hebrew
- Automatic positioning (screen-aware)
- Configurable display delay and duration

Author: Frontend UI Developer
Version: 1.0.0
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect
from PyQt6.QtGui import QIcon, QScreen

from src.resources.icons import IconLibrary

logger = logging.getLogger(__name__)


class HelpTooltip(QWidget):
    """
    Custom tooltip widget with rich formatting support.

    Unlike standard QToolTip, this provides:
    - Full control over styling and theming
    - RTL layout support for Hebrew
    - Rich HTML content rendering
    - Optional icons and titles
    - Configurable delays and durations

    Features:
    - Auto-positions near target widget
    - Respects screen boundaries
    - RTL-aware positioning
    - Auto-hides on mouse leave or timeout
    """

    # Default values (can be overridden by settings)
    DEFAULT_DELAY_MS = 500
    DEFAULT_DURATION_MS = 5000
    MAX_WIDTH = 400

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the tooltip widget.

        Args:
            parent: Optional parent widget
        """
        # Create as a tooltip window (frameless, stays on top)
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)

        self.setObjectName("help_tooltip")

        # State
        self._target_widget: Optional[QWidget] = None
        self._show_timer: Optional[QTimer] = None
        self._hide_timer: Optional[QTimer] = None
        self._widgets_created: bool = False

        # Widget references (created lazily)
        self.frame: Optional[QFrame] = None
        self.content_layout: Optional[QVBoxLayout] = None
        self.header_widget: Optional[QWidget] = None
        self.header_layout: Optional[QHBoxLayout] = None
        self.icon_label: Optional[QLabel] = None
        self.title_label: Optional[QLabel] = None
        self.text_label: Optional[QLabel] = None

        # Use default values (can be overridden per tooltip via show_for_widget)
        self._delay_ms = self.DEFAULT_DELAY_MS
        self._duration_ms = self.DEFAULT_DURATION_MS

        # Set window properties and size constraints (minimal setup)
        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setMaximumWidth(self.MAX_WIDTH)

    def _ensure_widgets(self) -> None:
        """Create widgets lazily on first use (performance optimization)."""
        if self._widgets_created:
            return

        self._init_ui()
        self._widgets_created = True

    def _init_ui(self) -> None:
        """Initialize the user interface (called lazily by _ensure_widgets)."""

        # Main container frame (for border/styling)
        self.frame = QFrame(self)
        self.frame.setObjectName("tooltip_frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)

        # Container layout
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.frame)

        # Content layout inside frame
        self.content_layout = QVBoxLayout(self.frame)
        self.content_layout.setContentsMargins(12, 10, 12, 10)
        self.content_layout.setSpacing(8)

        # Header (optional - for icon + title)
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(8)

        # Icon (optional)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        self.icon_label.setScaledContents(True)
        self.icon_label.hide()  # Hidden by default
        self.header_layout.addWidget(self.icon_label)

        # Title (optional)
        self.title_label = QLabel()
        self.title_label.setObjectName("tooltip_title")
        font = self.title_label.font()
        font.setBold(True)
        font.setPointSize(10)
        self.title_label.setFont(font)
        self.title_label.hide()  # Hidden by default
        self.header_layout.addWidget(self.title_label)

        self.header_layout.addStretch()
        self.header_widget.hide()  # Hidden by default

        self.content_layout.addWidget(self.header_widget)

        # Content text
        self.text_label = QLabel()
        self.text_label.setObjectName("tooltip_text")
        self.text_label.setWordWrap(True)
        self.text_label.setTextFormat(Qt.TextFormat.RichText)
        self.text_label.setOpenExternalLinks(False)
        font = self.text_label.font()
        font.setPointSize(9)
        self.text_label.setFont(font)
        self.content_layout.addWidget(self.text_label)

        # Styling is now handled by QSS theme files
        # (light_theme.qss and dark_theme.qss)

    def set_content(
        self,
        text: str,
        title: Optional[str] = None,
        icon: Optional[QIcon] = None,
        icon_name: Optional[str] = None
    ) -> None:
        """
        Set the tooltip content.

        Args:
            text: Main tooltip text (supports HTML)
            title: Optional title text
            icon: Optional QIcon to display
            icon_name: Optional icon name from IconLibrary
        """
        # Ensure widgets are created before accessing them
        self._ensure_widgets()

        # Set text content
        self.text_label.setText(text)

        # Set title if provided
        if title:
            self.title_label.setText(title)
            self.title_label.show()
            self.header_widget.show()
        else:
            self.title_label.hide()

        # Set icon if provided
        if icon:
            pixmap = icon.pixmap(16, 16)
            self.icon_label.setPixmap(pixmap)
            self.icon_label.show()
            self.header_widget.show()
        elif icon_name:
            try:
                pixmap = IconLibrary.get_pixmap(icon_name, size=(16, 16))
                self.icon_label.setPixmap(pixmap)
                self.icon_label.show()
                self.header_widget.show()
            except Exception as e:
                logger.warning(f"Failed to load icon '{icon_name}': {e}")
                self.icon_label.hide()
        else:
            self.icon_label.hide()

        # Hide header if no title or icon
        if not title and not (icon or icon_name):
            self.header_widget.hide()

        # Adjust size to content
        self.adjustSize()

    def show_for_widget(
        self,
        widget: QWidget,
        delay_ms: Optional[int] = None,
        duration_ms: Optional[int] = None
    ) -> None:
        """
        Show the tooltip near the specified widget after a delay.

        Args:
            widget: Target widget to show tooltip for
            delay_ms: Optional delay before showing (uses default if None)
            duration_ms: Optional auto-hide duration (uses default if None)
        """
        if not widget:
            logger.warning("Cannot show tooltip: widget is None")
            return

        # Ensure widgets are created before showing
        self._ensure_widgets()

        self._target_widget = widget

        # Use provided delays or defaults
        show_delay = delay_ms if delay_ms is not None else self._delay_ms
        hide_duration = duration_ms if duration_ms is not None else self._duration_ms

        # Cancel any existing timers
        self._cancel_timers()

        # Create show timer
        self._show_timer = QTimer(self)
        self._show_timer.setSingleShot(True)
        self._show_timer.timeout.connect(self._show_tooltip)
        self._show_timer.start(show_delay)

        # Create hide timer (starts after tooltip is shown)
        if hide_duration > 0:
            self._hide_timer = QTimer(self)
            self._hide_timer.setSingleShot(True)
            self._hide_timer.timeout.connect(self.hide_tooltip)

    def _show_tooltip(self) -> None:
        """Show the tooltip at the calculated position."""
        if not self._target_widget:
            return

        # Calculate position near target widget
        position = self._calculate_position()
        self.move(position)

        # Show the tooltip
        self.show()

        # Start hide timer if configured
        if self._hide_timer and self._duration_ms > 0:
            self._hide_timer.start(self._duration_ms)

        logger.debug(f"Showing tooltip at {position}")

    def _calculate_position(self) -> QPoint:
        """
        Calculate the optimal position for the tooltip.

        Takes into account:
        - Target widget position
        - Screen boundaries
        - RTL layout direction

        Returns:
            QPoint for tooltip position
        """
        if not self._target_widget:
            return QPoint(0, 0)

        # Get target widget global rect
        widget_rect = self._target_widget.rect()
        widget_global_pos = self._target_widget.mapToGlobal(widget_rect.topLeft())
        widget_global_rect = QRect(widget_global_pos, widget_rect.size())

        # Get tooltip size
        tooltip_size = self.sizeHint()

        # Get screen geometry
        screen = self._get_screen_for_widget(self._target_widget)
        screen_rect = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

        # Check if RTL layout
        is_rtl = self.layoutDirection() == Qt.LayoutDirection.RightToLeft

        # Calculate horizontal position
        if is_rtl:
            # RTL: Show tooltip to the left of widget
            x = widget_global_rect.right() - tooltip_size.width()
        else:
            # LTR: Show tooltip to the right of widget (or centered below)
            x = widget_global_rect.left()

        # Calculate vertical position (below widget by default)
        y = widget_global_rect.bottom() + 8

        # Create initial position
        position = QPoint(x, y)

        # Adjust if tooltip would go off-screen horizontally
        if position.x() + tooltip_size.width() > screen_rect.right():
            position.setX(screen_rect.right() - tooltip_size.width() - 10)
        if position.x() < screen_rect.left():
            position.setX(screen_rect.left() + 10)

        # Adjust if tooltip would go off-screen vertically
        if position.y() + tooltip_size.height() > screen_rect.bottom():
            # Show above widget instead
            position.setY(widget_global_rect.top() - tooltip_size.height() - 8)

        return position

    def _get_screen_for_widget(self, widget: QWidget) -> Optional[QScreen]:
        """
        Get the screen containing the widget.

        Args:
            widget: Widget to find screen for

        Returns:
            QScreen object or None
        """
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                widget_center = widget.mapToGlobal(widget.rect().center())
                return app.screenAt(widget_center)
        except Exception as e:
            logger.warning(f"Failed to get screen for widget: {e}")

        return None

    def hide_tooltip(self) -> None:
        """Hide the tooltip and clean up."""
        self._cancel_timers()
        self.hide()
        logger.debug("Tooltip hidden")

    def _cancel_timers(self) -> None:
        """Cancel any active timers."""
        if self._show_timer:
            self._show_timer.stop()
            self._show_timer = None

        if self._hide_timer:
            self._hide_timer.stop()
            self._hide_timer = None

    def leaveEvent(self, event) -> None:
        """
        Handle mouse leave event.

        Hides the tooltip when mouse leaves.

        Args:
            event: Leave event
        """
        self.hide_tooltip()
        super().leaveEvent(event)

    def enterEvent(self, event) -> None:
        """
        Handle mouse enter event.

        Cancels auto-hide timer when mouse enters tooltip.

        Args:
            event: Enter event
        """
        # Cancel hide timer if mouse enters tooltip
        if self._hide_timer:
            self._hide_timer.stop()

        super().enterEvent(event)

    def sizeHint(self):
        """
        Get the recommended size for the tooltip.

        Returns:
            QSize for tooltip
        """
        # If widgets haven't been created yet, return a default size
        if not self._widgets_created or not self.layout():
            from PyQt6.QtCore import QSize
            return QSize(200, 100)

        # Let the layout calculate the optimal size
        return self.layout().sizeHint()

    # Theme styling is now handled by QSS theme files
    # (light_theme.qss and dark_theme.qss)
    # The set_theme() method has been removed


# Convenience function for showing quick tooltips
def show_help_tooltip(
    widget: QWidget,
    text: str,
    title: Optional[str] = None,
    icon_name: Optional[str] = None,
    delay_ms: Optional[int] = None,
    duration_ms: Optional[int] = None
) -> HelpTooltip:
    """
    Show a help tooltip for a widget.

    Convenience function for quick tooltip display.

    Args:
        widget: Target widget to show tooltip for
        text: Tooltip text (supports HTML)
        title: Optional title text
        icon_name: Optional icon name from IconLibrary
        delay_ms: Optional delay before showing
        duration_ms: Optional auto-hide duration

    Returns:
        HelpTooltip instance
    """
    tooltip = HelpTooltip(widget)
    tooltip.set_content(text, title=title, icon_name=icon_name)
    tooltip.show_for_widget(widget, delay_ms=delay_ms, duration_ms=duration_ms)
    return tooltip
