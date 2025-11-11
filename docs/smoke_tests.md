# Smoke Test Checklist

- [ ] Run `python manage.py migrate` to ensure schema is intact.
- [ ] Create a planting activity with realistic inputs; confirm forecast appears with min/avg/max and harvest window.
- [ ] Open planting detail from Activity Log and Forecast card; verify same numbers and factor breakdown.
- [ ] Use “Recalculate Forecast” and confirm success flash + updated Forecast record.
- [ ] Add/edit/delete expenses; check confirmation modals and flash messages.
- [ ] Filter expenses by Month + Year and download CSV/PDF; confirm contents match the filtered view.
- [ ] Validate expense charts: line (axis labels, legend), donut (legend with %), bar (color mapping).
- [ ] Walk through Forgot Password flow end-to-end using console email backend.
- [ ] Login as technician; verify banner, technician home page, links to farmer dashboard.
- [ ] Delete reminder via modal; ensure HTMX refresh and flash message appear.
- [ ] Review mobile layouts on responsive emulator (≤390px) for dashboard, activity log, and expense log (no horizontal scrolling).

