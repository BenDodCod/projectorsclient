# Latest Session Context: 2026-02-15

## Quick Summary
Comprehensive help system improvements: dark mode support, window position persistence, layout optimization.

## What Works Now
✅ Help window moves freely and remembers position across sessions  
✅ Help window doesn't block main app (can go behind it)  
✅ Dark mode: Text colors adapt automatically (readable in both modes)  
✅ WhatsNew dialog: Optimized layout (20px margins, 251px left, dynamic sizing)  
✅ Related Topics: Dynamic height, narrower margins  
✅ Off-screen safety: Window repositions if off-screen after resolution change  

## Key Technical Changes
- **Removed** `addDockWidget()` call - allows free window movement
- **Manual position tracking**: Save `{x, y, width, height}` as JSON
- **Save on close/hide only**: Not during drag (prevents interference)
- **Dark mode detection**: Via palette luminance analysis
- **Adaptive colors**: Light text in dark mode, dark text in light mode

## Files Modified (3)
- `src/ui/main_window.py` (+61, -18)
- `src/ui/help/help_panel.py` (+93, -23)
- `src/ui/help/whats_new_dialog.py` (+76, -12)

## Testing Status
- Unit tests: 261 passed ✅
- PyInstaller build: Succeeded ✅
- Manual testing: Required in exe

## Known Issues
None - all reported issues resolved.

## Next Session Should
1. Test PyInstaller exe manually
2. Verify position persistence works in exe
3. Continue with next roadmap item

## Quick Reference
Full session details: `docs/REVIEWS/2026/2026-02-15-session.md`
