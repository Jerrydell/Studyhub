# 📖 Phase 3 - Quick Reference Guide

## 🔗 URL Routes

### Subjects
- **List All**: `/subjects`
- **Create**: `/subject/new`
- **View**: `/subject/<id>`
- **Edit**: `/subject/<id>/edit`
- **Delete**: `/subject/<id>/delete` (POST)

### Notes
- **Create**: `/subject/<subject_id>/note/new`
- **View**: `/note/<id>`
- **Edit**: `/note/<id>/edit`
- **Delete**: `/note/<id>/delete` (POST)

### Dashboard
- **Main**: `/dashboard` (shows subjects and recent notes)

---

## 🗄️ Database Models

### Subject
```python
{
    'id': int,
    'name': str (max 100),
    'description': str (optional),
    'color': str (hex color, default #0d6efd),
    'user_id': int (foreign key),
    'created_at': datetime,
    'notes': relationship to Note
}
```

### Note
```python
{
    'id': int,
    'title': str (max 200),
    'content': str (required),
    'subject_id': int (foreign key),
    'created_at': datetime,
    'updated_at': datetime,
    'subject': relationship to Subject
}
```

---

## 🎨 Template Variables

### subjects/list.html
- `subjects`: List of Subject objects

### subjects/view.html
- `subject`: Subject object
- `notes`: List of Note objects

### subjects/form.html
- `form`: SubjectForm
- `action`: 'Create' or 'Update'
- `subject`: Subject object (edit only)

### notes/form.html
- `form`: NoteForm
- `subject`: Subject object
- `action`: 'Create' or 'Update'
- `note`: Note object (edit only)

### notes/view.html
- `note`: Note object

### dashboard.html
- `subjects`: List of Subject objects
- `recent_notes`: List of Note objects
- `total_subjects`: int
- `total_notes`: int

---

## 🔒 Security Checks

Every subject/note route includes:
```python
if subject.user_id != current_user.id:
    abort(403)
```

---

## 💡 Helper Methods

### Subject Model
```python
subject.note_count  # Returns number of notes
```

### Note Model
```python
note.preview  # Returns first 100 chars of content
```

---

## 🎯 Form Validation

### SubjectForm
- Name: 2-100 chars, required
- Description: 0-500 chars, optional
- Color: Valid hex color

### NoteForm
- Title: 2-200 chars, required
- Content: Min 10 chars, required

---

## 🚀 Quick Commands

```bash
# Create/migrate database
python migrate_db.py

# Run application
python run.py

# Access in browser
http://localhost:5000
```

---

## 📝 Common Queries

### Get all subjects for current user
```python
subjects = current_user.subjects.all()
```

### Get all notes for a subject
```python
notes = subject.notes.all()
```

### Get recent notes across all subjects
```python
recent_notes = Note.query.join(Subject).filter(
    Subject.user_id == current_user.id
).order_by(Note.updated_at.desc()).limit(5).all()
```

---

## 🎨 Color Picker Usage

```html
<input type="color" value="#0d6efd">
```

Default colors:
- Blue: `#0d6efd` (Primary)
- Green: `#198754` (Success)
- Red: `#dc3545` (Danger)
- Yellow: `#ffc107` (Warning)
- Cyan: `#0dcaf0` (Info)

---

## ⌨️ Keyboard Shortcuts (in templates)

Press `Ctrl+S` in forms to submit (browser default)

---

## 🧹 Database Cleanup

```bash
# Delete database and start fresh
rm studyhub.db
python migrate_db.py
```

---

**Keep this guide handy while developing!** 📚
