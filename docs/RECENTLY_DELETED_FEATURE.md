# Recently Deleted Records Feature

## Overview
A comprehensive "Recently Deleted" feature has been implemented for the Railway Wagon Inspection System. This feature provides a safety net for deleted inspection records by keeping them for 7 days before permanent deletion.

## Features Implemented

### 1. **Soft Delete System**
- When users delete a session, it's moved to a separate deleted sessions folder
- Deleted sessions are retained for **7 days** before automatic permanent deletion
- Metadata is updated with deletion timestamp

### 2. **Two-Tab Interface**
The Records page now has two tabs:

#### **Active Records Tab** 📋
- Shows all current inspection sessions
- Normal delete operation (moves to Recently Deleted)
- Same functionality as before

#### **Recently Deleted Tab** 🗑️
- Shows all deleted sessions from the past 7 days
- Displays deletion timestamp
- Shows countdown to permanent deletion
- Badge indicator showing number of deleted items

### 3. **User Actions**

#### On Active Records:
- **Delete** - Moves session to Recently Deleted (soft delete)

#### On Recently Deleted Records:
- **Restore** ↩️ - Restores the session back to Active Records
- **Delete Permanently** ⚠️ - Permanently removes the session (cannot be undone)

### 4. **Visual Indicators**
- Information banner explaining 7-day retention policy
- Countdown timer showing days until permanent deletion
- Warning banner when viewing deleted session details
- Color-coded styling:
  - Orange accents for deleted items
  - Red for permanent delete warnings
  - Green for restore actions

## Technical Implementation

### Backend Changes (`backend/app.py`)

#### New Folder Structure:
```
sessions/           # Active sessions
sessions_deleted/   # Deleted sessions (7-day retention)
```

#### New API Endpoints:

1. **GET `/api/deleted-sessions`**
   - Returns all deleted sessions within 7 days
   - Includes days_until_permanent_delete counter

2. **POST `/api/session/<id>/restore`**
   - Restores a deleted session to active sessions
   - Removes deletion timestamp

3. **DELETE `/api/session/<id>/permanent-delete`**
   - Permanently deletes a session from deleted folder
   - Cannot be undone

4. **POST `/api/cleanup-old-deletions`**
   - Auto-cleanup endpoint for sessions older than 7 days
   - Can be called periodically via cron/scheduler

#### Modified Endpoints:

- **DELETE `/api/session/<id>`** - Changed to soft delete (moves to deleted folder instead of permanent deletion)

### Frontend Changes

#### HTML (`index.html`)
- Added tab navigation interface
- Created separate content areas for active and deleted records
- Added new modal for deleted session details
- New action buttons (Restore, Permanent Delete)

#### JavaScript (`script.js`)

**New State:**
```javascript
AppState.deletedSessions = []
AppState.currentRecordsTab = 'active'
```

**New Functions:**
- `switchRecordsTab(tab)` - Switch between Active and Deleted tabs
- `loadDeletedSessions()` - Fetch and display deleted sessions
- `updateDeletedRecordsPage()` - Render deleted sessions list
- `openDeletedSessionDetail(session)` - Show deleted session details
- `restoreCurrentSession()` - Restore a deleted session
- `permanentDeleteCurrentSession()` - Permanently delete with confirmation
- `apiGetDeletedSessions()` - API call for deleted sessions
- `apiRestoreSession(id)` - API call to restore
- `apiPermanentDeleteSession(id)` - API call to permanently delete

#### CSS (`style.css`)

**New Styles:**
- `.records-tabs` - Tab navigation container
- `.records-tab` - Individual tab styling
- `.tab-badge` - Count badge for deleted items
- `.deleted-info-banner` - Information banner
- `.deleted-session-item` - Styling for deleted session cards
- `.deleted-info` - Deletion timestamp display
- `.deleted-warning-banner` - Warning banner in modal
- `.restore-session-btn` - Green restore button
- `.permanent-delete-btn` - Red permanent delete button

## User Flow

### Deleting a Session:
1. User opens a session from Active Records
2. Clicks "🗑️ DELETE" button
3. Confirms deletion
4. Session moves to Recently Deleted tab
5. Badge counter updates

### Restoring a Session:
1. User switches to Recently Deleted tab
2. Opens a deleted session
3. Clicks "↩️ RESTORE" button
4. Session moves back to Active Records
5. Deletion timestamp removed

### Permanent Deletion:
1. User opens deleted session
2. Clicks "⚠️ DELETE PERMANENTLY"
3. Sees strong warning confirmation
4. Session is permanently removed
5. Cannot be recovered

### Auto-Cleanup:
After 7 days, sessions in Recently Deleted are automatically eligible for permanent deletion via the cleanup endpoint.

## Safety Features

1. **Confirmation Dialogs**
   - Soft delete: "Are you sure you want to move to recently deleted?"
   - Permanent delete: "⚠️ WARNING: This will PERMANENTLY delete... cannot be undone"

2. **Visual Warnings**
   - Orange warning banner in deleted sessions
   - Countdown timer showing auto-delete date
   - Color-coded danger styling for permanent actions

3. **7-Day Grace Period**
   - Sufficient time to recover accidentally deleted sessions
   - Automatic cleanup prevents storage bloat

## Future Enhancements (Optional)

1. **Scheduled Cleanup**
   - Add a cron job or scheduler to call `/api/cleanup-old-deletions` daily
   - Automatic removal of sessions older than 7 days

2. **Email Notifications**
   - Notify operators when their sessions are about to be permanently deleted
   - Daily digest of recently deleted items

3. **Bulk Operations**
   - Restore multiple sessions at once
   - Empty entire Recently Deleted folder

4. **Configurable Retention**
   - Allow admins to adjust the 7-day retention period
   - Per-session retention overrides

5. **Export Before Delete**
   - Option to download session data before permanent deletion
   - Backup deleted sessions to external storage

## How to Use

1. **Start the Backend:**
   ```bash
   cd railway_dashboard/backend
   python app.py
   ```

2. **Access Dashboard:**
   - Open browser to `http://localhost:5000`

3. **Navigate to Records:**
   - Click "RECORDS" from navigation or selection screen

4. **Switch Tabs:**
   - Click "ACTIVE RECORDS" or "RECENTLY DELETED" tabs

5. **Manage Sessions:**
   - Delete sessions from Active tab
   - Restore or permanently delete from Deleted tab

## Testing Checklist

- ✅ Delete session moves to Recently Deleted
- ✅ Deleted tab shows correct sessions
- ✅ Badge count updates correctly
- ✅ Countdown timer displays properly
- ✅ Restore moves session back to Active
- ✅ Permanent delete removes session completely
- ✅ Confirmation dialogs appear for all actions
- ✅ Visual styling matches design system
- ✅ API endpoints respond correctly
- ✅ Sessions older than 7 days filtered properly

## Notes

- All deleted sessions retain their complete data (images, metadata, detections)
- Restoration preserves all original session information
- The 7-day limit is calculated from the `deleted_at` timestamp
- Sessions are stored separately to prevent accidental access during active operations
