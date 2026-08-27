# Recently Deleted - Quick Reference

## 📋 Feature Overview

The Records page now has **two tabs**:
- **Active Records** - Current inspection sessions
- **Recently Deleted** - Deleted sessions (kept for 7 days)

---

## 🎯 Quick Actions

### From Active Records Tab:

```
Click Session → 🗑️ DELETE → Confirm
  ↓
Session moves to Recently Deleted
  ↓
Badge counter updates
```

### From Recently Deleted Tab:

#### Option 1: Restore
```
Click Deleted Session → ↩️ RESTORE
  ↓
Session returns to Active Records
  ↓
All data preserved
```

#### Option 2: Permanent Delete
```
Click Deleted Session → ⚠️ DELETE PERMANENTLY → Confirm Warning
  ↓
Session PERMANENTLY removed
  ↓
❌ CANNOT BE UNDONE
```

---

## 🕒 Auto-Deletion Timeline

```
Day 0: Session deleted
  ↓
Days 1-6: Available in Recently Deleted
  ↓
Day 7: Last day to restore
  ↓
Day 8: Auto-cleanup eligible
```

---

## 🎨 Visual Indicators

| Element | Color | Meaning |
|---------|-------|---------|
| 📋 Active Tab | Blue | Current records |
| 🗑️ Deleted Tab | Orange | Recently deleted |
| Badge Number | Orange | Count of deleted items |
| ℹ️ Info Banner | Orange | Retention policy notice |
| ⚠️ Warning Banner | Red | Permanent deletion warning |
| ↩️ Restore Button | Green | Safe action |
| ⚠️ Delete Permanently | Red | Danger action |

---

## 🔐 Safety Features

✅ **Two-Step Delete Process**
- First delete: Moves to Recently Deleted
- Second delete: Requires explicit confirmation

✅ **Warning Confirmations**
- Soft delete: Simple confirmation
- Permanent delete: Strong warning message

✅ **Visual Countdown**
- Shows days until auto-deletion
- Clear time indicators

✅ **7-Day Grace Period**
- Plenty of time to recover mistakes
- Automatic cleanup prevents clutter

---

## 📊 What's Preserved in Recently Deleted?

When a session is deleted, ALL data is retained:
- ✅ Session metadata (operator, date, type)
- ✅ Wagon detections and OCR results
- ✅ Deblurred frames
- ✅ Original images
- ✅ Damage detection data
- ✅ Complete inspection results

**Everything is restored** when you recover a session!

---

## 🚀 Keyboard Shortcuts

*(Future enhancement)*
- `D` - Delete selected session
- `R` - Restore selected session
- `Shift+Del` - Permanent delete
- `Tab` - Switch between tabs

---

## ⚡ Pro Tips

1. **Regular Reviews**: Check Recently Deleted weekly to recover important sessions

2. **Before Permanent Delete**: Double-check if you need the data exported

3. **Storage Management**: Let auto-cleanup handle old deletions automatically

4. **Accidental Deletes**: Don't panic! You have 7 days to restore

5. **Batch Operations**: Delete multiple old sessions from active, then clear Recently Deleted in one go

---

## 🔧 API Endpoints Reference

```javascript
// Get deleted sessions
GET /api/deleted-sessions

// Restore a session
POST /api/session/{id}/restore

// Permanent delete
DELETE /api/session/{id}/permanent-delete

// Manual cleanup (admin)
POST /api/cleanup-old-deletions
```

---

## ❓ FAQ

**Q: What happens after 7 days?**
A: Sessions become eligible for auto-cleanup. They won't appear in Recently Deleted anymore.

**Q: Can I extend the 7-day period?**
A: Currently fixed at 7 days. Can be made configurable in future updates.

**Q: What if I permanently delete by accident?**
A: Unfortunately, permanent deletion cannot be undone. Always double-check!

**Q: Does deletion affect storage immediately?**
A: No, soft delete doesn't free storage. Only permanent delete or auto-cleanup does.

**Q: Can I export before permanent delete?**
A: Not yet - this is a planned future enhancement.

---

## 🎯 Common Use Cases

### Scenario 1: Accidental Delete
1. Accidentally deleted important session
2. Switch to Recently Deleted tab
3. Find session (still there!)
4. Click Restore
5. ✅ Session back in Active Records

### Scenario 2: Spring Cleaning
1. Delete multiple old test sessions
2. Review in Recently Deleted
3. Restore any needed ones
4. Permanently delete the rest
5. ✅ Storage cleaned up

### Scenario 3: Quality Control
1. Delete low-quality inspection
2. Manager asks to review
3. Restore from Recently Deleted
4. Review and re-delete if confirmed
5. ✅ Proper review process followed
